"""One canonical unit of work: responsibility, eligibility, application and receipt."""
import hashlib
import json
import time
from uuid import uuid4
from sqlalchemy import update
from app.core.errors import AppError
from app.mercury.models import MercuryCase, SimulatedOrder
from app.mercury.aftersales_models import AfterSalesProposal, AfterSalesApplication, AfterSalesReceipt
from app.mercury import orders


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def fail(code, message, status=409):
    raise AppError(status, code, message)


class AfterSalesService:
    def __init__(self, sessions):
        self.sessions = sessions

    @staticmethod
    def _case(db, owner_id, case_id):
        # First statement is a write fence, so SQLite readers never upgrade a
        # stale snapshot. Human transitions use the same canonical case row.
        changed = db.execute(update(MercuryCase).where(MercuryCase.case_id == case_id,
            MercuryCase.owner_id == owner_id).values(selection_version=MercuryCase.selection_version)).rowcount
        if changed != 1:
            fail('NOT_FOUND', '未找到该售后会话', 404)
        return db.get(MercuryCase, case_id)

    @staticmethod
    def _agent(case, run_context=None):
        if case.responsibility != 'agent':
            fail('HUMAN_RESPONSIBILITY', '人工正在负责此事项，不能提交售后申请')
        if run_context is not None:
            if (case.active_run_id != run_context['run_id']
                or case.responsibility_generation != run_context['responsibility_generation']
                or case.active_until <= time.time()):
                fail('STALE_RUN', '本次处理已失效，请重新提出申请')
        elif case.active_run_id and case.active_until > time.time():
            fail('CASE_BUSY', '该事项正在处理，请稍后重试')

    @staticmethod
    def _latest(db, case_id):
        return db.query(AfterSalesProposal).filter_by(case_id=case_id).order_by(AfterSalesProposal.revision.desc()).first()

    @staticmethod
    def _facts(db, owner_id, case, kind, item_id, reason):
        order = db.query(SimulatedOrder).filter_by(owner_id=owner_id, order_id=case.order_id).first()
        if order is None:
            fail('ORDER_REQUIRED', '请先选择模拟订单')
        items = json.loads(order.snapshot_json)['items']
        applications = db.query(AfterSalesApplication).filter_by(order_id=order.order_id).all()
        if any(row.kind == 'refund' for row in applications):
            fail('ALREADY_REQUESTED', '此订单已有模拟退款申请，请查看回执')
        if kind == 'refund':
            if item_id is not None:
                fail('WHOLE_ORDER_ONLY', '仅退款只支持整单申请', 422)
            if applications:
                fail('ALREADY_REQUESTED', '此订单已有售后申请，请查看回执')
            if order.status not in ('submitted', 'paid'):
                fail('REFUND_INELIGIBLE', '此订单状态不支持未发货整单仅退款')
            chosen, amount, policy_id = items, order.total_fen, 'P-REF-01'
            condition = '仅限未发货整单模拟退款；申请不代表资金到账。'
        else:
            if not item_id:
                fail('ITEM_REQUIRED', '请选择要整行退货的商品', 422)
            chosen = [item for item in items if item['sku_id'] == item_id]
            if not chosen:
                fail('ITEM_NOT_FOUND', '订单中没有该商品', 404)
            if any(row.item_scope == item_id for row in applications):
                fail('ALREADY_REQUESTED', '此商品已有模拟退货申请，请查看回执')
            eligibility = orders.return_eligibility(order, chosen)['items'][0]
            if not eligibility['eligible']:
                fail(eligibility['reason_code'], eligibility['reason'])
            amount = chosen[0]['quantity'] * chosen[0]['unit_price_fen']
            policy_id = 'P-RET-01'
            condition = '签收后七天内且商品可退，仅整行模拟退货；提交时重新检查期限与资格。'
        facts = {'version': order.version, 'status': order.status, 'total_fen': order.total_fen,
                 'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
                 'snapshot': json.loads(order.snapshot_json)}
        preview = {'order_id': order.order_id, 'order_version': order.version, 'kind': kind,
            'item_id': item_id, 'reason': reason, 'amount_fen': amount,
            'items': [{'item_id': item['sku_id'], 'name': item['name'], 'quantity': item['quantity'],
                       'amount_fen': item['quantity'] * item['unit_price_fen']} for item in chosen],
            'policy_id': policy_id, 'policy': condition, 'simulated': True,
            'status': 'awaiting_confirmation'}
        return preview, hashlib.sha256(encoded(facts).encode()).hexdigest()

    def accept_replacement(self, owner_id, case_id, request, run_context=None):
        # Invalid input is not accepted intent and cannot discard a preview.
        if not request['reason'].strip():
            fail('REASON_REQUIRED', '请说明售后申请原因', 422)
        if request['kind'] == 'refund' and request['item_id'] is not None:
            fail('WHOLE_ORDER_ONLY', '仅退款只支持整单申请', 422)
        if request['kind'] == 'return' and not request['item_id']:
            fail('ITEM_REQUIRED', '请选择要整行退货的商品', 422)
        with self.sessions() as db:
            case = self._case(db, owner_id, case_id)
            self._agent(case, run_context)
            if case.selection_version != request['selection_version']:
                fail('STALE_SELECTION', '订单选择已变化，请重新查看提案')
            case.aftersales_intent_version += 1
            latest = self._latest(db, case_id)
            if latest and not db.query(AfterSalesReceipt).filter_by(proposal_id=latest.proposal_id).first():
                latest.invalidated = True
            # Accepted replacement invalidates old consent even if the next
            # eligibility node denies it. No application or receipt is written.
            db.commit()
            return case.aftersales_intent_version

    @staticmethod
    def _intent(case, accepted_version):
        if case.aftersales_intent_version != accepted_version:
            fail('STALE_INTENT', '申请意图已被更新，请查看最新请求')

    def eligibility(self, owner_id, case_id, request, accepted_version, run_context=None):
        with self.sessions() as db:
            case = self._case(db, owner_id, case_id)
            self._agent(case, run_context)
            self._intent(case, accepted_version)
            if case.selection_version != request['selection_version']:
                fail('STALE_SELECTION', '订单选择已变化，请重新查看提案')
            preview, _ = self._facts(db, owner_id, case, request['kind'], request['item_id'], request['reason'])
            return preview

    def propose(self, owner_id, case_id, request, proposal_id, accepted_version, run_context=None):
        with self.sessions() as db:
            case = self._case(db, owner_id, case_id)
            self._agent(case, run_context)
            self._intent(case, accepted_version)
            if case.selection_version != request['selection_version']:
                fail('STALE_SELECTION', '订单选择已变化，请重新查看提案')
            preview, facts_hash = self._facts(db, owner_id, case, request['kind'], request['item_id'], request['reason'])
            latest = self._latest(db, case_id)
            proposal = AfterSalesProposal(proposal_id=proposal_id, owner_id=owner_id,
                case_id=case_id, order_id=case.order_id, revision=latest.revision+1 if latest else 1,
                selection_version=case.selection_version, responsibility_generation=case.responsibility_generation,
                facts_hash=facts_hash, preview_json=encoded(preview))
            db.add(proposal)
            db.commit()
            return {**preview, 'proposal_id': proposal.proposal_id, 'revision': proposal.revision}

    @staticmethod
    def _replay(db, owner_id, case_id, proposal_id, key):
        receipt = db.query(AfterSalesReceipt).filter_by(owner_id=owner_id, idempotency_key=key).first()
        if receipt is None:
            return None
        if receipt.case_id != case_id or receipt.proposal_id != proposal_id:
            fail('IDEMPOTENCY_CONFLICT', '确认编号已经用于不同申请')
        return json.loads(receipt.result_json)

    def replay(self, owner_id, case_id, proposal_id, key):
        with self.sessions() as db:
            self._case(db, owner_id, case_id)
            return self._replay(db, owner_id, case_id, proposal_id, key)

    def submit(self, owner_id, case_id, proposal_id, key):
        with self.sessions() as db:
            case = self._case(db, owner_id, case_id)
            replay = self._replay(db, owner_id, case_id, proposal_id, key)
            if replay is not None:
                return replay
            self._agent(case)
            proposal = db.query(AfterSalesProposal).filter_by(owner_id=owner_id,case_id=case_id,proposal_id=proposal_id).first()
            if proposal is None:
                fail('NOT_FOUND', '未找到该申请提案', 404)
            if (proposal.invalidated or self._latest(db, case_id).proposal_id != proposal_id or case.order_id != proposal.order_id
                or case.selection_version != proposal.selection_version
                or case.responsibility_generation != proposal.responsibility_generation):
                fail('STALE_PROPOSAL', '提案或事项已变化，请重新查看并确认')
            if db.query(AfterSalesReceipt).filter_by(proposal_id=proposal_id).first():
                fail('ALREADY_CONFIRMED', '提案已提交，请查看原回执')
            preview = json.loads(proposal.preview_json)
            fresh, facts_hash = self._facts(db, owner_id, case, preview['kind'], preview['item_id'], preview['reason'])
            if fresh != preview or facts_hash != proposal.facts_hash:
                fail('STALE_FACTS', '订单或资格已变化，请生成新提案后确认')
            application = AfterSalesApplication(application_id=f'asa-{uuid4().hex}', owner_id=owner_id,
                case_id=case_id,proposal_id=proposal_id,order_id=case.order_id,kind=preview['kind'],
                item_scope=preview['item_id'] or '*',amount_fen=preview['amount_fen'],status='requested')
            db.add(application)
            db.flush()
            result = {**preview, 'status':'requested','proposal_id':proposal_id,
                'application_id':application.application_id,'receipt_id':f'asr-{uuid4().hex}',
                'message':'模拟售后申请已提交，尚未审批或退款到账；没有真实资金或履约操作。'}
            db.add(AfterSalesReceipt(receipt_id=result['receipt_id'], owner_id=owner_id,
                case_id=case_id,proposal_id=proposal_id,application_id=application.application_id,
                idempotency_key=key,result_json=encoded(result)))
            db.commit()
            return result

    def read(self, owner_id, case_id):
        with self.sessions() as db:
            case = db.query(MercuryCase).filter_by(owner_id=owner_id,case_id=case_id).first()
            if case is None:
                fail('NOT_FOUND', '未找到该售后会话', 404)
            latest = self._latest(db, case_id)
            receipts = [json.loads(row.result_json) for row in db.query(AfterSalesReceipt).filter_by(owner_id=owner_id,case_id=case_id)]
            proposal = None
            if latest and not latest.invalidated and latest.selection_version == case.selection_version and latest.responsibility_generation == case.responsibility_generation and case.responsibility == 'agent' and not any(row['proposal_id'] == latest.proposal_id for row in receipts):
                proposal = {**json.loads(latest.preview_json), 'proposal_id':latest.proposal_id, 'revision':latest.revision}
            return {'proposal':proposal,'receipts':receipts,'simulated':True}

    def record_failure(self, owner_id, case_id, error, *, selection_version=None, proposal_id=None):
        """Keep a safe, order-bound explanation in existing conversation history.

        This is not application status or permission. Canonical proposals and
        receipts remain the only business truth, including after response loss.
        """
        descriptions = {
            'NOT_DELIVERED': '订单尚未签收，不能申请签收商品退货',
            'DELIVERY_TIME_UNKNOWN': '签收时间未知，不能确定退货期限',
            'RETURN_WINDOW_EXPIRED': '已超过七天退货期限',
            'POLICY_UNKNOWN': '商品退货政策未知，不能确定资格',
            'NOT_RETURNABLE': '此商品不支持退货',
            'REFUND_INELIGIBLE': '当前订单状态不支持未发货整单退款',
            'ALREADY_REQUESTED': '该事项已有模拟申请，请查看原回执',
            'STALE_FACTS': '订单或资格已变化，需要重新查看提案',
            'STALE_PROPOSAL': '提案或事项已变化，需要重新查看提案',
            'HUMAN_RESPONSIBILITY': '人工正在负责此事项',
        }
        if isinstance(error, AppError):
            code = error.detail['error']['code']
            if code not in descriptions:
                return  # Invalid input, foreign identifiers and stale requests do not write history.
            explanation = descriptions[code]
        else:
            explanation = '售后服务暂时失败'
        with self.sessions() as db:
            changed = db.execute(update(MercuryCase).where(MercuryCase.case_id == case_id,
                MercuryCase.owner_id == owner_id).values(selection_version=MercuryCase.selection_version)).rowcount
            if changed != 1:
                return
            case = db.get(MercuryCase, case_id)
            if not case.order_id or (case.active_run_id and case.active_until > time.time()):
                return  # The active query owns publication of its own failure.
            if proposal_id is not None:
                proposal = db.query(AfterSalesProposal).filter_by(owner_id=owner_id,
                    case_id=case_id, proposal_id=proposal_id).first()
                if proposal is None or proposal.order_id != case.order_id or proposal.selection_version != case.selection_version:
                    return
                receipt = db.query(AfterSalesReceipt).filter_by(owner_id=owner_id,
                    case_id=case_id, proposal_id=proposal_id).first()
            else:
                if selection_version != case.selection_version:
                    return
                receipt = None
            if receipt:
                message = f'订单 {case.order_id}：提交响应未完整返回；已查到模拟申请回执 {receipt.receipt_id}，尚未审批或退款到账。不会自动重提。'
            else:
                message = f'订单 {case.order_id}：{explanation}；本次申请未提交，处理已暂停。可选择继续购物，购物不会重试此申请。'
            messages = json.loads(case.messages_json)
            entry = {'role': 'assistant', 'content': message}
            if not messages or messages[-1] != entry:
                case.messages_json = encoded([*messages, entry])
                db.commit()
