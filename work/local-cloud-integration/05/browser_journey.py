"""Tester-only real Chromium/public HTTP journey over the synthetic loopback fixture.

No live-provider or retrieval-quality claim. Run through launch_browser_fixture.py.
"""
import argparse
import base64
import ipaddress
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--chromium',required=True)
    parser.add_argument('--artifacts',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads(Path(os.environ['FIXTURE_MANIFEST']).read_text())
    base=manifest['base_url'];scenarios=manifest['scenarios']
    assert ipaddress.ip_address(urlsplit(base).hostname).is_loopback
    args.artifacts.mkdir(parents=True,exist_ok=True)
    calls=[];blocked=[];checks=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1100,'height':1000},service_workers='block')
        def guard(route):
            url=urlsplit(route.request.url)
            allowed=url.scheme in ('data','about','blob')
            if url.scheme in ('http','https'):
                try: allowed=ipaddress.ip_address(url.hostname).is_loopback
                except ValueError: allowed=url.hostname=='localhost'
            if allowed: route.continue_()
            else: blocked.append(route.request.url);route.abort()
        context.route('**/*',guard)
        context.add_cookies([manifest['cookie']])
        page=context.new_page()
        page.on('request',lambda request:calls.append({'url':request.url,'method':request.method,'body':request.post_data}) if '/api/' in request.url else None)
        def api(path):
            return page.evaluate("async path => {const r=await fetch(path);if(!r.ok)throw new Error(path+':'+r.status);return r.json()}",path)
        def screenshot(name): page.screenshot(path=str(args.artifacts/(name+'.png')),full_page=True)
        def close_chat():
            close=page.get_by_role('button',name='关闭聊天',exact=True)
            if close.is_visible():close.click()
        def send(text,role='可可'):
            field=page.get_by_placeholder('问问'+role+'吧…');expect(field).to_be_enabled();field.fill(text);field.press('Enter')
        def settled(): expect(page.get_by_role('button',name='停止本次处理',exact=True)).to_have_count(0,timeout=25000)
        def open_keke():
            close_chat();page.get_by_role('button',name='商品',exact=True).click();page.get_by_role('button',name='问问可可',exact=True).click();expect(page.get_by_placeholder('问问可可吧…')).to_be_enabled()
        def stream_count():return sum(row['url'].endswith('/turns/stream') for row in calls)
        try:
            page.goto(base);page.get_by_role('button',name='商品',exact=True).click()
            name=manifest['product']['name']
            page.get_by_role('button',name='查看'+name+'详情',exact=True).click()
            detail=page.get_by_role('dialog',name='商品详情');expect(detail).to_contain_text('模拟数据')
            before=api('/api/v1/cart');assert not before['items']
            detail.get_by_role('button',name='添加一件到购物车',exact=True).click()
            expect(detail.get_by_role('button',name='添加一件到购物车',exact=True)).to_be_enabled()
            cart=api('/api/v1/cart');assert len(cart['items'])==1 and cart['items'][0]['quantity']==1
            screenshot('01-product-detail');detail.get_by_role('button',name='关闭',exact=True).click()
            page.get_by_role('button',name='购物车',exact=True).click();page.get_by_role('button',name='结算',exact=True).click()
            checkout=page.get_by_role('dialog',name='模拟结算');expect(checkout).to_contain_text('不会付款或真实配送')
            checkout.get_by_role('button',name='确认模拟结算',exact=True).click();expect(checkout).to_contain_text('模拟订单已保存')
            order=next(row for row in api('/api/v1/orders')['items'] if row['order_id'] not in manifest['order_ids'])
            snapshot=order['items'];amount=order['total_fen']
            checkout.get_by_role('button',name='查看订单',exact=True).click();page.get_by_role('button',name='查看订单 '+order['order_id'],exact=True).click()
            page.get_by_role('button',name='模拟推进至配送中',exact=True).click();page.get_by_role('button',name='模拟签收',exact=True).click()
            expect(page.locator('[data-order-id]')).to_contain_text('delivered')
            final=api('/api/v1/orders/'+order['order_id']);assert final['items']==snapshot and final['total_fen']==amount
            checks.append('product explicit add/checkout and immutable demo progression');screenshot('02-order-snapshot')
            page.get_by_role('button',name='联系墨墨',exact=True).click();expect(page.get_by_label('售后类型')).to_be_enabled()
            case=page.evaluate("localStorage.getItem('ceres-mercury-case')")
            assert api('/api/v1/mercury/sessions/'+case)['order_id']==order['order_id']
            page.get_by_label('售后类型').select_option('quality');page.get_by_label('退货商品').select_option(manifest['product']['sku_id'])
            page.get_by_label('问题销售包装数').fill('1');page.get_by_label('售后原因').fill('受控演示包装破损')
            # Synthetic one-pixel PNG; no personal image input.
            png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGPgEpEDAABoAD1UCKP3AAAAAElFTkSuQmCC')
            page.get_by_label('质量问题照片').set_input_files({'name':'synthetic.png','mimeType':'image/png','buffer':png})
            expect(page.get_by_alt_text('待人工核对的照片',exact=True)).to_have_count(1)
            page.get_by_role('button',name='查看申请提案',exact=True).click();expect(page.locator('[data-proposal-id]')).to_contain_text('质量问题登记')
            page.get_by_role('button',name='确认提交此模拟申请',exact=True).click()
            ticket=page.get_by_text('异步人工工单',exact=False).first;ticket.click()
            expect(page.get_by_alt_text('待核对的问题照片',exact=True)).to_have_count(1)
            human=api('/api/v1/mercury/sessions/'+case+'/human-ticket');assert len(human['applications'])==1 and len(human['photos'])==1
            checks.append('explicit quality count/photo confirmation and ticket evidence');screenshot('03-ticket-evidence')
            # Re-contact the same order after close: no redundant selection/version bump.
            selected=api('/api/v1/mercury/sessions/'+case);close_chat()
            page.get_by_role('button',name='查看订单 '+order['order_id'],exact=True).click();page.get_by_role('button',name='联系墨墨',exact=True).click()
            expect(page.get_by_placeholder('问问墨墨吧…')).to_be_enabled()
            assert api('/api/v1/mercury/sessions/'+case)['selection_version']==selected['selection_version']
            checks.append('same-order contact preserves canonical version')
            open_keke();send(scenarios['yes']);expect(page.get_by_role('button',name='切换并继续原请求',exact=True)).to_be_visible()
            count=stream_count();page.get_by_role('button',name='留在这里',exact=True).click()
            page.get_by_role('button',name='墨墨 · 订单售后',exact=True).click();expect(page.get_by_placeholder('问问墨墨吧…')).to_be_enabled();assert stream_count()==count
            checks.append('yes rejection and pure role button do not replay')
            open_keke();send(scenarios['yes']);page.get_by_role('button',name='切换并继续原请求',exact=True).click();expect(page.get_by_placeholder('问问墨墨吧…')).to_be_enabled();checks.append('yes acceptance enters Momo')
            open_keke()
            for outcome in ('no','uncertain','error','timeout'):
                greetings=page.get_by_text('你好，这是受控浏览器演示。',exact=True)
                prior=greetings.count();send(scenarios[outcome]);expect(greetings).to_have_count(prior+1,timeout=25000);settled()
            checks.append('Coco negative/uncertain/provider fallback continues original')
            send(scenarios['mixed']);expect(page.get_by_role('button',name='前往墨墨处理',exact=True).last).to_be_visible(timeout=25000);settled();screenshot('04-mixed-result')
            count=stream_count();page.get_by_role('button',name='前往墨墨处理',exact=True).last.click();expect(page.get_by_placeholder('问问墨墨吧…')).to_be_enabled();assert stream_count()==count
            checks.append('mixed policy and explicit role action without replay')
            open_keke();send(scenarios['interim']);expect(page.get_by_text('我先核对演示商品，再说明下一步。',exact=True).last).to_be_visible(timeout=25000);settled()
            sid=page.evaluate("sessionStorage.getItem('ceres-langgraph-guide-session-id')")
            history=api('/api/v1/guide/sessions/'+sid+'?include_messages=1')['messages'];ids=[row['message_id'] for row in history];assert len(ids)==len(set(ids))
            page.reload();expect(page.get_by_placeholder('问问可可吧…')).to_be_enabled();settled();screenshot('05-interim-restored')
            assert [row['message_id'] for row in api('/api/v1/guide/sessions/'+sid+'?include_messages=1')['messages']]==ids
            checks.append('reviewed interims and reload preserve stable history without writes')
            send(scenarios['slow']);expect(page.get_by_role('button',name='停止本次处理',exact=True)).to_be_visible();page.get_by_role('button',name='停止本次处理',exact=True).click();settled();checks.append('explicit stop ends client delivery')
            screenshot('06-stopped')
            send(scenarios['typed']);category=page.get_by_role('region',name='想看哪类饮品？',exact=True)
            expect(category).to_be_visible(timeout=25000);settled();category.get_by_role('button').first.click()
            choices=page.get_by_role('region',name='请选择商品和销售包装数量，选定后再核对清单。',exact=True).last
            expect(choices.get_by_role('checkbox').first).to_be_enabled();choices.get_by_role('checkbox').first.check()
            choices.get_by_role('spinbutton').first.fill('1');choices.get_by_role('button',name='生成采购清单',exact=True).click()
            expect(choices.get_by_text('已回答',exact=True)).to_be_visible()
            answers=[row for row in calls if '/questions/' in row['url'] and row['url'].endswith('/answers')]
            assert len(answers)>=2 and all(json.loads(row['body'])['option_ids'] for row in answers)
            assert not api('/api/v1/cart')['items'];checks.append('native typed category/checkbox/quantity creates plan without cart write')
            screenshot('07-typed-plan')
            print(json.dumps({'ok':True,'level':'real-Chromium-controlled-loopback-backend','checks':checks,'boundaries':manifest['boundaries'],'blocked_external_requests':blocked},ensure_ascii=False))
        except Exception:
            screenshot('failure');raise
        finally:
            (args.artifacts/'requests.json').write_text(json.dumps(calls,ensure_ascii=False,indent=2))
            (args.artifacts/'network-blocks.json').write_text(json.dumps(blocked,indent=2))
            browser.close()

if __name__=='__main__':main()
