"""Tester-only real public business HTTP contracts on fresh synthetic loopback fixture."""
import base64
import ipaddress
import json
import os
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit

manifest=json.loads(Path(os.environ['FIXTURE_MANIFEST']).read_text())
base=manifest['base_url'];assert ipaddress.ip_address(urlsplit(base).hostname).is_loopback
cookie=manifest['cookie'];reads=[]
def call(path,body=None,expected=200,operator=False,method=None):
    headers={'Content-Type':'application/json','Cookie':cookie['name']+'='+cookie['value']}
    if operator:headers['X-Internal-Token']=manifest['operator_token']
    request=Request(base+path,data=None if body is None else json.dumps(body).encode(),headers=headers,method=method or ('GET' if body is None else 'POST'))
    try:
        with urlopen(request,timeout=20) as response:status=response.status;raw=response.read();kind=response.headers.get('Content-Type','')
    except HTTPError as error:status=error.code;raw=error.read();kind=error.headers.get('Content-Type','')
    reads.append({'path':path,'status':status});assert status==expected,(path,status,raw[:500])
    return json.loads(raw) if 'json' in kind else raw
sku=manifest['product']['sku_id'];product=call('/api/v1/products/'+sku);assert product['sellable']
cart=call('/api/v1/cart');assert not cart['items']
cart=call('/api/v1/cart/items',{'sku_id':sku,'quantity':1,'expected_cart_version':cart['version']})
preview=call('/api/v1/checkout/preview',{'expected_cart_version':cart['version']})
confirm={'preview_id':preview['preview_id'],'idempotency_key':'t05-http-checkout','confirmed':True}
receipt=call('/api/v1/checkout/confirm',confirm);assert call('/api/v1/checkout/confirm',confirm)==receipt
order=receipt['order'];items=order['items'];amount=order['total_fen'];path='/api/v1/orders/'+order['order_id']
call(path+'/demo-state',{'expected_version':order['version'],'status':'delivered'},409)
body={'expected_version':order['version'],'status':'shipped'};order=call(path+'/demo-state',body)
call(path+'/demo-state',body,409)
order=call(path+'/demo-state',{'expected_version':order['version'],'status':'delivered'})
assert order['items']==items and order['total_fen']==amount
case=call('/api/v1/mercury/sessions',{})['session_id'];root='/api/v1/mercury/sessions/'+case
current=call(root);current=call(root+'/order',{'order_id':order['order_id'],'selection_version':current['selection_version']},method='PUT')
png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGPgEpEDAABoAD1UCKP3AAAAAElFTkSuQmCC'
photo=call(root+'/photos',{'content_type':'image/png','data_base64':png,'selection_version':current['selection_version']})
body={'kind':'quality','item_id':sku,'reason':'受控模拟包装破损','selection_version':current['selection_version'],'problem_quantity':2,'photo_ids':[photo['photo_id']]}
call(root+'/proposals',body,422);body['problem_quantity']=1
proposal=call(root+'/proposals',body);assert proposal['photo_ids']==[photo['photo_id']]
confirm={'proposal_id':proposal['proposal_id'],'idempotency_key':proposal['proposal_id'],'confirmed':True}
receipt=call(root+'/confirm',confirm);assert call(root+'/confirm',confirm)==receipt
state=call(root+'/aftersales');assert len(state['receipts'])==1
human=call(root+'/human-ticket');assert len(human['applications'])==1 and [p['photo_id'] for p in human['photos']]==[photo['photo_id']]
assert call('/api/v1/mercury/operator/tickets/'+human['ticket_id']+'/photos/'+photo['photo_id'],operator=True)==base64.b64decode(png)
print(json.dumps({'ok':True,'level':'real-public-HTTP-synthetic-loopback','checks':['explicit product/cart','checkout idempotency','ordered demo progression/stale version','immutable order snapshots','quality count rejection','photo proposal/confirmation idempotency','exact ticket evidence'], 'requests':reads,'boundaries':manifest['boundaries']},ensure_ascii=False))
