"""Explicit synthetic browser fixture; product application code is unchanged.

Real FastAPI, Pi SDK and LangGraph run against loopback scripted models. Retrieval
is a controlled KnowledgeService.search port, NOT BGE/GraphRAG acceptance.
"""
import argparse
from datetime import datetime, timezone, timedelta
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import sqlite3
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

from launch_browser_fixture import refuse_dotenv

SCENARIOS={
    'yes':'[BROWSER:YES] 查询已下单订单的退货问题',
    'no':'[BROWSER:NO] 打个招呼',
    'uncertain':'[BROWSER:UNCERTAIN] 打个招呼',
    'error':'[BROWSER:ERROR] 打个招呼',
    'timeout':'[BROWSER:TIMEOUT] 打个招呼',
    'mixed':'[BROWSER:MIXED] 查饮品和一般退货政策，具体订单问题另交墨墨',
    'interim':'[BROWSER:INTERIM] 查饮品信息，不加购',
    'slow':'[BROWSER:SLOW] 先提示正在查询，再慢慢查询饮品信息',
    'typed':'[BROWSER:TYPED] 选饮品类型，再明确选择商品数量',
    'quality':'[BROWSER:QUALITY] 申请登记这件商品一个销售包装的质量问题',
}


def install_safety():
    def loopback(host):
        if host in ('localhost',b'localhost'):
            return True
        try:
            return ipaddress.ip_address(host.decode() if isinstance(host,bytes) else host).is_loopback
        except (ValueError,TypeError):
            return False
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
            if Path(os.fsdecode(args[0])).name=='.env':
                raise PermissionError('FIXTURE_DENIES_DOTENV_READ')
        if event in ('socket.connect','socket.bind') and isinstance(args[1],tuple):
            if not loopback(args[1][0]):
                raise PermissionError('FIXTURE_DENIES_NON_LOOPBACK_NETWORK')
        if event=='socket.getaddrinfo' and not loopback(args[0]):
            raise PermissionError('FIXTURE_DENIES_EXTERNAL_DNS')
    sys.addaudithook(audit)


def tool(name,arguments,content=None):
    result={'role':'assistant','tool_calls':[{'id':'browser-'+name,'type':'function',
        'function':{'name':name,'arguments':json.dumps(arguments,ensure_ascii=False)}}]}
    if content:
        result['content']=content
    return result


def message_text(message):
    content=message.get('content','')
    if isinstance(content,str):
        return content
    if isinstance(content,list):
        return ''.join(block['text'] for block in content if block['type']=='text')
    raise TypeError('Unsupported controlled-provider content envelope')


def model_answer(body,product):
    messages=body['messages']
    system='\n'.join(message_text(row) for row in messages if row['role']=='system')
    users=[message_text(row) for row in messages if row['role']=='user']
    user=next((value for value in reversed(users) if not value.startswith('CERES_POLICY_EVIDENCE')), '')
    outputs=[json.loads(row['content']) for row in messages if row['role']=='tool']
    if 'CERES_INTERIM_CLAIM_CHECK' in system:
        return {'role':'assistant','content':json.dumps({'merchant_claims':False,'execution_claims':False,'private_content':False})}
    if 'CERES_GENERAL_CLAIM_CHECK' in system:
        return {'role':'assistant','content':json.dumps({'merchant_claims':False,'execution_claims':False})}
    if body.get('stream') and not body.get('tools'):
        # Actual expression-only Pi is a distinct no-tool public caller. It
        # still validates this neutral introduction and renders host facts.
        payload=json.loads(user)
        facts=payload['facts']
        return {'role':'assistant','content':json.dumps({'text':'以下是本次已核对的结果。','fact_ref':next(iter(facts))},ensure_ascii=False)+'\n'}
    # Mercury uses the real graph and the same real OpenAI client in nonstream mode.
    if not body.get('stream'):
        match=re.search(r'当前选定订单：([^\n]+)',system)
        order_id=match.group(1) if match else ''
        if not order_id or order_id=='None':
            return {'role':'assistant','content':'请选择模拟订单。'}
        last_user=max((index for index,row in enumerate(messages) if row['role']=='user'),default=-1)
        if any(row['role']=='tool' for row in messages[last_user+1:]):
            return {'role':'assistant','content':'已读取本次工具结果。'}
        if '[BROWSER:QUALITY]' in user:
            return tool('prepare_aftersales_proposal',{'order_id':order_id,'kind':'quality',
                'item_id':product['sku_id'],'problem_quantity':1,'reason':user})
        return tool('get_order_details',{'order_id':order_id})
    if not outputs:
        active=any(marker in user for marker in ('[BROWSER:TYPED]','[BROWSER:MIXED]'))
        args={'kind':'new_goal','goal':'选购演示饮品'} if active else {'kind':'question'}
        return tool('guide_request',args,'我先核对演示商品，再说明下一步。' if any(marker in user for marker in ('[BROWSER:INTERIM]','[BROWSER:SLOW]','[BROWSER:MIXED]')) else None)
    if '[BROWSER:SLOW]' in user and len(outputs)==1:
        time.sleep(12)  # Allows stop/reload after an already audited message.
    if '[BROWSER:TYPED]' in user:
        if len(outputs)==1:
            return tool('explore_products',{'category_id':'beverage'})
        return tool('finish_response',{'status':'completed','answer_kind':'exploration','exploration_ref':outputs[-1]['exploration_ref']})
    if any(marker in user for marker in ('[BROWSER:MIXED]','[BROWSER:INTERIM]','[BROWSER:SLOW]')):
        if len(outputs)==1:
            return tool('search_products',{'category_id':'beverage'},'我继续核对可展示的商品信息。' if '[BROWSER:INTERIM]' in user else None)
        result={'status':'completed','answer_kind':'products','product_refs':[row['ref'] for row in outputs[-1]['products'][:2]]}
        if '[BROWSER:MIXED]' in user:
            evidence=next(json.loads(value.split('\n',1)[1]) for value in users if value.startswith('CERES_POLICY_EVIDENCE\n'))
            result.update(policy_ref=evidence['policy_ref'],role_boundary=True)
        return tool('finish_response',result)
    if len(outputs)==1:
        return tool('validate_general_text',{'messages':['你好，这是受控浏览器演示。']})
    return tool('finish_response',{'status':'completed','answer_kind':'general_explanation','general_ref':outputs[-1]['general_ref']})


def provider_server(product):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if self.path.endswith('/systemone'):
                purpose=next(iter(body['questions']))
                text=json.dumps(body['state'],ensure_ascii=False)
                if purpose=='service' and '[BROWSER:ERROR]' in text:
                    self.send_error(503,'Controlled Kev unavailable')
                    return
                if purpose=='service' and '[BROWSER:TIMEOUT]' in text:
                    time.sleep(4)
                choice='yes' if ('[BROWSER:YES]' in text and purpose=='service') or ('[BROWSER:MIXED]' in text and purpose=='policy') else 'uncertain' if '[BROWSER:UNCERTAIN]' in text and purpose=='service' else 'no'
                self.send_json({'model':'kev-latest','answers':{purpose:{'type':'choice','choice':choice,
                    'probabilities':{key:float(key==choice) for key in ('yes','no','uncertain')}}}})
                return
            if not self.path.endswith('/chat/completions'):
                self.send_error(404)
                return
            message=model_answer(body,product)
            if not body.get('stream'):
                self.send_json({'id':'browser-model','object':'chat.completion','created':int(time.time()),
                    'model':body['model'],'choices':[{'index':0,'message':message,'finish_reason':'tool_calls' if message.get('tool_calls') else 'stop'}]})
                return
            for index,call in enumerate(message.get('tool_calls',[])):
                call['index']=index
            try:
                self.send_response(200)
                self.send_header('Content-Type','text/event-stream')
                self.end_headers()
                reason='tool_calls' if message.get('tool_calls') else 'stop'
                for delta,finish in ((message,None),({},reason)):
                    chunk={'id':'browser-model','object':'chat.completion.chunk','created':int(time.time()),
                        'model':body['model'],'choices':[{'index':0,'delta':delta,'finish_reason':finish}]}
                    self.wfile.write(('data: '+json.dumps(chunk,ensure_ascii=False)+'\n\n').encode())
                self.wfile.write(b'data: [DONE]\n\n')
            except (BrokenPipeError,ConnectionResetError):
                pass  # Expected when real cancellation closes its provider request.
        def send_json(self,payload):
            try:
                raw=json.dumps(payload,ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError):
                pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    server.daemon_threads=True
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--frontend-dist',type=Path,required=True)
    parser.add_argument('--runtime-dir',type=Path,required=True)
    args=parser.parse_args()
    source=args.source.resolve(); runtime=args.runtime_dir.resolve()
    refuse_dotenv(source)
    install_safety()
    sys.path.insert(0,str(source/'backend'))
    from app.core.config import Settings,get_settings
    Settings.model_config['env_file']=None
    get_settings.cache_clear()
    products=json.loads((source/'data/fixtures/products.json').read_text())['products']
    product=next(row for row in products if row['category_id']=='beverage' and row['review_status']=='approved')
    provider=provider_server(product)
    os.environ['OPENAI_BASE_URL']=f'http://127.0.0.1:{provider.server_port}/v1'
    os.environ['KEV_BASE_URL']=f'http://127.0.0.1:{provider.server_port}'
    from app.core.database import engine,init_db,SessionLocal
    from app.services.seed_service import seed_catalog
    from app.models.identity import Owner
    from app.models.store import Offer
    from app.mercury.models import SimulatedOrder
    from sqlalchemy import select
    init_db()
    now=datetime.now(timezone.utc)
    owner='browser-synthetic-owner'
    order_ids=['browser-delivered-a','browser-delivered-b']
    with SessionLocal.begin() as db:
        seed_catalog(db,source/'data/fixtures')
        db.add(Owner(id=owner));db.flush()
        offer=db.scalar(select(Offer).where(Offer.sku_id==product['sku_id'],Offer.store_id=='store-demo-01'))
        offer.available_qty=max(offer.available_qty,20);offer.sellable=True
        item={'sku_id':product['sku_id'],'name':product.get('name_zh') or product['name'],
            'quantity':2,'unit_price_fen':offer.price_fen,'returnable':True,'return_policy_source':'browser-synthetic-fixture'}
        for identity in order_ids:
            db.add(SimulatedOrder(order_id=identity,owner_id=owner,store_id='store-demo-01',status='delivered',
                snapshot_json=json.dumps({'items':[item],'store_id':'store-demo-01','total_fen':offer.price_fen*2},ensure_ascii=False),total_fen=offer.price_fen*2,
                created_at=now-timedelta(days=1),delivered_at=now-timedelta(hours=1)))
    # A newly generated provenance-only manifest supports explicit simulated
    # recall. No production/old runtime index or database is copied or opened.
    from app.knowledge.corpus import FIXTURE_NAMES,load_corpus
    from app.knowledge.hybrid import build_parameters
    from app.services.knowledge_service import knowledge,check_budget
    from app.mercury import policy
    fixtures=runtime/'controlled-source/data/fixtures';fixtures.mkdir(parents=True)
    for name in FIXTURE_NAMES:
        shutil.copyfile(source/'data/fixtures'/name,fixtures/name)
    documents,manifest=load_corpus(fixtures);manifest.update(build_parameters())
    index=runtime/'controlled-source/data/indexes/hybrid.sqlite3';index.parent.mkdir()
    with sqlite3.connect(index) as db:
        db.execute('CREATE TABLE manifest (content TEXT)')
        db.execute('INSERT INTO manifest VALUES (?)',(json.dumps(manifest),))
    policy.get_settings=lambda:SimpleNamespace(root_dir=runtime/'controlled-source')
    def controlled_search(query,namespace,*,limit=10,allowed_ids=None,category=None,deadline=None,should_stop=None,expected_index_revision=None):
        if deadline is not None:
            check_budget(deadline,should_stop)
        if namespace not in ('product','policy'):
            raise ValueError('Browser fixture does not simulate GraphRAG or recipe recall')
        rows=[row for row in documents if row['namespace']==namespace and (allowed_ids is None or row['id'] in allowed_ids)
            and (category is None or row.get('category')==category)]
        if namespace=='product' and query:
            rows=[row for row in rows if query.lower() in (row['title']+' '+row['text']).lower()]
        # Policy is an explicit deterministic controlled ranking, not relevance proof.
        return {'manifest':manifest,'hits':[{'id':row['id'],'document':row,'ranks':{'controlled':rank},
            'scores':{'controlled':1.0},'rrf_score':1/(60+rank)} for rank,row in enumerate(rows[:limit],1)]}
    knowledge.search=controlled_search
    # Explicit fixture-only disablement: no memory-worker acceptance claimed.
    from app.services.memory_background import MemoryWorker
    MemoryWorker.start=lambda self:None
    MemoryWorker.stop=lambda self:None
    from app.main import create_app
    from fastapi.staticfiles import StaticFiles
    app=create_app()
    from fastapi.responses import RedirectResponse
    from fastapi import HTTPException, Request
    @app.get('/__fixture__/start')
    def synthetic_browser_start(request:Request):
        if request.headers.get('host')!=browser_authority:
            raise HTTPException(403,'Fixture bootstrap requires its unique browser Host')
        response=RedirectResponse('/',status_code=303)
        response.set_cookie('sg_owner_id',owner,httponly=True,samesite='lax',max_age=900)
        return response
    @app.middleware('http')
    async def same_origin_only(request,call_next):
        response=await call_next(request)
        response.headers['Content-Security-Policy']=(
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; img-src 'self' data: blob:; font-src 'self' data:; "
            "media-src 'self' blob:; worker-src 'self' blob:; frame-src 'none'; "
            "object-src 'none'; base-uri 'self'; form-action 'self'")
        response.headers['X-Test-Fixture']='isolated-loopback-browser'
        return response
    app.mount('/',StaticFiles(directory=args.frontend_dist,html=True),name='browser-fixture-ui')
    sock=socket.socket();sock.bind(('127.0.0.1',0));sock.listen(128)
    port=sock.getsockname()[1]
    base_url=f'http://127.0.0.1:{port}'
    browser_authority=f'ceres-fixture-{secrets.token_hex(12)}.localhost:{port}'
    browser_url='http://'+browser_authority
    metadata={'base_url':base_url,'browser_url':browser_url,'product':{'sku_id':product['sku_id'],'name':product.get('name_zh') or product['name']},
        'owner_id':owner,'cookie':{'name':'sg_owner_id','value':owner,'url':browser_url},
        'order_ids':order_ids,'second_order_id':order_ids[1],'operator_token':'browser-synthetic-operator-token',
        'scenarios':SCENARIOS,'boundaries':{'models':'scripted loopback HTTP; real Pi SDK and LangGraph',
            'retrieval':'controlled KnowledgeService.search port; no BGE/GraphRAG quality claim',
            'memory':'background worker explicitly disabled; no memory acceptance',
            'data':'fresh SQLite/checkpoint and versioned synthetic demo fixtures only'}}
    import uvicorn
    # create_app owns a lifespan, so readiness is emitted by an independent
    # polling thread only after the actual public health endpoint is accepting.
    def ready_when_serving():
        import urllib.request
        end=time.monotonic()+35
        while time.monotonic()<end:
            try:
                with urllib.request.urlopen(base_url+'/health',timeout=.5) as response:
                    if json.load(response)['status']=='ok':
                        pending=runtime/'ready.pending.json'
                        pending.write_text(json.dumps(metadata,ensure_ascii=False))
                        pending.replace(runtime/'ready.json')
                        return
            except (OSError,TimeoutError):
                time.sleep(.1)
    threading.Thread(target=ready_when_serving,daemon=True).start()
    try:
        uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=0,log_level='warning',timeout_graceful_shutdown=3)).run(sockets=[sock])
    finally:
        provider.shutdown();provider.server_close();sock.close()


if __name__=='__main__':
    main()
