"""Explain a committed result without re-entering routing or business services."""
import hashlib
import json
import time
from uuid import uuid4
from sqlalchemy import func, select, update
from sqlalchemy.orm import sessionmaker

from app.core.errors import AppError
from app.models.guide import GuideSession, GuideTask, GuideCommandReceipt, GuideTurnReceipt, GuideMessage
from app.services.pi_product_turn_service import owned_session, session_anchor
from app.services.guide_run_service import EXECUTION_ID, TERMINAL, append_event, start_worker, run_cancelled
from app.services.result_expression_runtime import generate_introduction


def _source(db, owner_id, session_id, kind, source_id):
    if kind == 'question_answer':
        row = db.get(GuideCommandReceipt, (session_id, source_id))
        selection = db.scalar(select(GuideMessage).where(GuideMessage.session_id==session_id, GuideMessage.owner_id==owner_id, GuideMessage.request_id==source_id, GuideMessage.kind=='selection'))
        if row is None or selection is None:
            raise AppError(404, 'RESULT_NOT_FOUND', '没有找到本次已完成的选择结果')
        result = json.loads(row.result_json)
        question = result.get('active_question')
        if question:
            count = len(question['options'])
            fact = f'本次找到 {count} 款可选商品，价格和库存为模拟数据。' if question['kind']=='products' else question['question']
        elif result.get('plan'):
            fact = '本次清单已准备好，尚未加购。价格和库存为模拟数据。'
        else:
            fact = '本次没有匹配商品，尚未加购。价格和库存为模拟数据。'
        return result, {'result':fact, 'next_step':'选好商品和销售包装数量后，还需要单独确认加购。'}, None
    if kind == 'purchase_confirmation':
        from app.models.purchase import PurchaseConfirmation
        row = db.get(PurchaseConfirmation, (owner_id, source_id))
        task = db.get(GuideTask, row.task_id) if row else None
        if row is None or task is None or task.session_id != session_id:
            raise AppError(404, 'RESULT_NOT_FOUND', '没有找到本次加购回执')
        result = json.loads(row.result_json)
        count = sum(item['quantity'] for item in result['items_added'])
        return result, {'result':f'本次已将 {count} 件销售包装加入购物车（模拟业务）。', 'next_step':'加购尚未下单或付款。'}, None
    if kind == 'turn':
        row = db.scalar(select(GuideTurnReceipt).where(GuideTurnReceipt.owner_id==owner_id, GuideTurnReceipt.session_id==session_id, GuideTurnReceipt.request_id==source_id))
        if row is None or row.status not in ('completed','waiting_confirmation') or not row.result_json:
            raise AppError(404, 'RESULT_NOT_FOUND', '没有找到本次已完成的结果')
        result = json.loads(row.result_json)
        if result.get('answer_kind') in ('result_introduction','general_explanation') or result.get('runtime_status')!='completed':
            raise AppError(422, 'RESULT_KIND_UNSUPPORTED', '这个结果不需要介绍')
        if result.get('confirmation_result'):
            count=sum(item['quantity'] for item in result['confirmation_result']['items_added'])
            fact=f'本次已将 {count} 件销售包装加入购物车（模拟业务）。'
        elif result.get('active_question') and result['active_question']['question_id']==result.get('assistant_message_id'):
            question=result['active_question']
            fact=f"本次找到 {len(question['options'])} 款可选商品，价格和库存为模拟数据。" if question['kind']=='products' else question['question']
        elif result.get('plan_effect')=='replace' and result.get('plan'):
            fact='本次清单已准备好，尚未加购。价格和库存为模拟数据。'
        elif result.get('no_matches'):
            fact='本次没有查到匹配商品，价格和库存为模拟数据。'
        elif result.get('product_evidence') or result.get('product_cards'):
            count=len(result.get('product_cards') or result['product_evidence'])
            fact=f'本次找到 {count} 款商品，价格和库存为模拟数据。'
        else:
            raise AppError(422, 'RESULT_KIND_UNSUPPORTED', '这个结果不需要介绍')
        return result, {'result':fact}, None
    if kind == 'aftersales_receipt':
        from app.mercury.aftersales_models import AfterSalesReceipt, AfterSalesProposal
        from app.mercury.models import MercuryCase
        row=db.get(AfterSalesReceipt,source_id)
        if row is None or row.owner_id!=owner_id:
            raise AppError(404,'RESULT_NOT_FOUND','没有找到本次模拟申请回执')
        case=db.get(MercuryCase,row.case_id)
        proposal=db.get(AfterSalesProposal,row.proposal_id)
        if case.order_id!=proposal.order_id or case.selection_version!=proposal.selection_version or case.responsibility_generation!=proposal.responsibility_generation or case.responsibility!='agent':
            raise AppError(409,'RESULT_STALE','售后对象已变化，原申请回执仍保留')
        anchor=session_anchor(db,owned_session(db,owner_id,session_id))
        result={**json.loads(row.result_json),'session_version':anchor[0],'task_id':anchor[1],'state_version':anchor[2]}
        case_anchor={'case_id':case.case_id,'order_id':case.order_id,'selection_version':case.selection_version,'responsibility_generation':case.responsibility_generation,'aftersales_intent_version':case.aftersales_intent_version, 'messages_digest':hashlib.sha256(case.messages_json.encode()).hexdigest()}
        return result, {'result':result['message'],'next_step':'这是一份模拟申请回执，不代表退款已经到账。'}, case_anchor
    raise AppError(422, 'RESULT_KIND_UNSUPPORTED', '这个结果暂不支持介绍')


def start_introduction(db, owner_id, session_id, body):
    from app.services.guide_lifecycle_service import require_canonical_session
    from app.services.navigation_service import metadata
    session = owned_session(db, owner_id, session_id)
    require_canonical_session(db, owner_id, session_id)
    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    request_id = 'intro-' + digest[:32]
    db.execute(update(GuideSession).where(GuideSession.session_id==session_id, GuideSession.owner_id==owner_id).values(session_version=GuideSession.session_version))
    db.expire_all()
    existing = db.scalar(select(GuideTurnReceipt).where(GuideTurnReceipt.session_id==session_id, GuideTurnReceipt.request_id==request_id))
    if existing:
        recorded = json.loads(existing.input_json)
        if existing.owner_id != owner_id or existing.digest != digest or recorded.get('kind') != 'result_introduction' or recorded.get('source') != body:
            raise AppError(409, 'IDEMPOTENCY_CONFLICT', '这个请求标识属于其他处理，原结果仍保留')
        db.commit()
        return {'run_id':existing.run_id,'request_id':request_id,'session_id':session_id}
    source, facts, case_anchor = _source(db, owner_id, session_id, body['source_kind'], body['source_id'])
    session = owned_session(db, owner_id, session_id)
    anchor = session_anchor(db, session)
    if anchor != (source['session_version'],source['task_id'],source['state_version']):
        raise AppError(409, 'RESULT_STALE', '已有结果仍保留，请查看当前任务')
    opening = metadata(session)
    if opening and (opening['closed'] or opening['role']!=('momo' if case_anchor else 'keke')):
        raise AppError(409, 'RESULT_STALE', '聊天角色已变化，已有结果仍保留')
    message_sequence = db.scalar(select(func.max(GuideMessage.sequence)).where(GuideMessage.session_id==session_id,GuideMessage.kind!='introduction')) or 0
    run_id = 'run-' + uuid4().hex
    payload = {'kind':'result_introduction', 'source':body, 'facts':facts, 'opening':opening, 'message_sequence':message_sequence, 'case_anchor':case_anchor, 'role':'momo' if case_anchor else 'keke'}
    result = {'session_id':session_id,'task_id':anchor[1],'session_version':anchor[0],'state_version':anchor[2],
              'request_id':request_id,'answer_kind':'result_introduction','messages':[], 'message':'',
              'source':body,'business_result':source,'runtime_status':'running','expression_status':'running'}
    receipt = GuideTurnReceipt(run_id=run_id,owner_id=owner_id,session_id=session_id,request_id=request_id,digest=digest,status='running',input_json=json.dumps(payload,ensure_ascii=False),anchor_json=json.dumps({'session_version':anchor[0],'task_id':anchor[1],'state_version':anchor[2]}),result_json=json.dumps(result,ensure_ascii=False),execution_id=EXECUTION_ID,started_at=time.time())
    db.add(receipt);db.flush()
    append_event(db,receipt,'accepted',{'request_id':request_id,'kind':'result_introduction'})
    append_event(db,receipt,'result.ready',{'source':body,'result':source})
    db.commit()
    factory=sessionmaker(bind=db.get_bind(),autoflush=False,expire_on_commit=False)
    deadline=time.monotonic()+(15.0 if case_anchor else 30.0)
    start_worker(db.get_bind(),run_id,deadline,lambda:_introduce(factory,owner_id,session_id,run_id,deadline))
    return {'run_id':run_id,'request_id':request_id,'session_id':session_id}


def _introduce(factory,owner_id,session_id,run_id,deadline):
    with factory() as db:
        receipt=db.get(GuideTurnReceipt,run_id)
        original=json.loads(receipt.anchor_json)
        inputs=json.loads(receipt.input_json)
        facts=inputs['facts']
        message_id='intro-msg-'+uuid4().hex
        published=set()
        stopped_reason='stopped'

        def current():
            nonlocal stopped_reason
            if time.monotonic() >= deadline:
                stopped_reason='deadline'
                return False
            db.expire_all()
            row=db.get(GuideTurnReceipt,run_id)
            if run_cancelled(run_id) or row.status!='running':
                return False
            session=owned_session(db,owner_id,session_id)
            from app.services.navigation_service import metadata
            anchor=session_anchor(db,session)
            if inputs['case_anchor']:
                from app.mercury.models import MercuryCase
                case=db.get(MercuryCase,inputs['case_anchor']['case_id'])
                if case.responsibility!='agent' or any(getattr(case,key)!=value for key,value in inputs['case_anchor'].items() if key!='messages_digest') or hashlib.sha256(case.messages_json.encode()).hexdigest()!=inputs['case_anchor']['messages_digest'] or case.active_run_id:
                    stopped_reason='stale'
                    return False
            latest_message=db.scalar(select(func.max(GuideMessage.sequence)).where(GuideMessage.session_id==session_id,GuideMessage.kind!='introduction')) or 0
            newer=db.scalar(select(GuideTurnReceipt.run_id).where(GuideTurnReceipt.session_id==session_id,GuideTurnReceipt.started_at>row.started_at).limit(1))
            if anchor!=(original['session_version'],original['task_id'],original['state_version']) or metadata(session)!=inputs['opening'] or latest_message!=inputs['message_sequence'] or newer:
                stopped_reason='stale'
                return False
            if time.monotonic() >= deadline:
                stopped_reason='deadline'
                return False
            return True

        def should_stop():
            active=current()
            db.rollback()
            return not active

        def unit(text,fact_ref):
            if len(published)>=2 or fact_ref in published:
                raise AppError(422,'EXPRESSION_UNIT_INVALID','介绍引用重复或过多')
            # Lock the same session as every task/navigation action before the
            # final freshness check and event/history publication.
            db.execute(update(GuideSession).where(GuideSession.session_id==session_id,GuideSession.owner_id==owner_id).values(session_version=GuideSession.session_version))
            if not current():
                db.rollback()
                return
            row=db.get(GuideTurnReceipt,run_id)
            result=json.loads(row.result_json)
            delta=facts[fact_ref]+text
            content=result['message']+delta
            history=db.get(GuideMessage,message_id)
            if inputs['case_anchor']:
                pass  # Mercury keeps its own history; only this expression receipt is updated.
            elif history is None:
                sequence=(db.scalar(select(func.max(GuideMessage.sequence)).where(GuideMessage.session_id==session_id)) or 0)+1
                history=GuideMessage(message_id=message_id,session_id=session_id,owner_id=owner_id,task_id=original['task_id'],sequence=sequence,role='assistant',kind='introduction',content=content,request_id=row.request_id)
                db.add(history)
            else:
                history.content=content
            result.update(message=content,messages=[{'message_id':message_id,'content':content}])
            row.result_json=json.dumps(result,ensure_ascii=False)
            append_event(db,row,'answer.delta',{'delta':delta,'replace':not published,'final':False,'message_id':message_id,'answer_kind':'result_introduction','fact_ref':fact_ref,'source':inputs['source'],'published_at_ms':time.time()*1000})
            db.commit();published.add(fact_ref)

        def metric(value):
            if should_stop():
                return
            row=db.get(GuideTurnReceipt,run_id)
            append_event(db,row,'expression.metric',value)
            db.commit()

        try:
            status=generate_introduction(run_id,facts,role=inputs['role'],deadline=deadline,should_stop=should_stop,on_unit=unit,on_metric=metric)
            if status=='stopped':
                status=stopped_reason
        except Exception as exc:
            db.rollback()
            # Only the expression is failed. The original command/transaction
            # receipt is never touched and no retry enters business services.
            from app.services.guide_run_service import log_host_failure
            log_host_failure(run_id,exc)
            status='failed'
        db.expire_all()
        row=db.get(GuideTurnReceipt,run_id)
        if row.status in TERMINAL:
            return
        result=json.loads(row.result_json)
        result.update(runtime_status='completed',expression_status=status)
        row.result_json=json.dumps(result,ensure_ascii=False)
        row.status='completed'
        append_event(db,row,'turn.completed',result)
        db.commit()
