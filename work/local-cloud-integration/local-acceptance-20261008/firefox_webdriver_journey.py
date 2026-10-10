"""Real system Firefox journey through an exact-authority loopback proxy.

This tester-owned harness uses the production UI, Pi SDK and LangGraph with the
tracked controlled provider/retrieval fixture. It is not live-provider or RAG-
quality evidence. Every browser HTTP/CONNECT request passes through a local
proxy which forwards only the fixture's unique host and blocks other hosts.
"""
from __future__ import annotations

import argparse
import base64
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import threading
import time
from urllib.parse import urlsplit

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait


def xpath_string(value: str) -> str:
    if "'" not in value:
        return "'" + value + "'"
    if '"' not in value:
        return '"' + value + '"'
    return "concat(" + ", \"'\", ".join("'" + part + "'" for part in value.split("'")) + ")"


class ExactFixtureProxy:
    def __init__(self, target_authority: str, target_port: int, cert_file: Path, key_file: Path):
        self.target_authority = target_authority.lower()
        self.target_port = target_port
        self.rows: list[dict] = []
        self.lock = threading.Lock()
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_context.load_cert_chain(str(cert_file), str(key_file))

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            server_version = 'CeresFixtureProxy/1'
            sys_version = ''

            def log_message(self, *_args):
                return

            def _row(self, row):
                with owner.lock:
                    owner.rows.append(row)

            def do_CONNECT(self):
                authority = self.path.lower()
                allowed = authority == owner.target_authority
                self._row({'method': 'CONNECT', 'authority': authority, 'allowed': allowed,
                           'action': 'terminate-tls-to-loopback' if allowed else 'blocked'})
                if not allowed:
                    self.send_response(403)
                    self.send_header('Content-Length', '0')
                    self.send_connection_close()
                    return
                try:
                    self.wfile.write(b'HTTP/1.1 200 Connection Established\r\nProxy-Agent: CeresFixtureProxy/1\r\n\r\n')
                    self.wfile.flush()
                    tls_socket = owner.ssl_context.wrap_socket(self.connection, server_side=True)
                    self.connection = tls_socket
                    self.rfile = tls_socket.makefile('rb', self.rbufsize)
                    self.wfile = tls_socket.makefile('wb', self.wbufsize)
                    self._fixture_tls_tunnel = True
                    self.close_connection = False
                except (ssl.SSLError, OSError):
                    self.close_connection = True

            def send_connection_close(self):
                self.send_header('Connection', 'close')
                self.end_headers()
                self.close_connection = True

            def _forward(self):
                parsed = urlsplit(self.path)
                if parsed.scheme:
                    scheme = parsed.scheme
                    authority = parsed.netloc.lower()
                    request_path = parsed.path or '/'
                    if parsed.query:
                        request_path += '?' + parsed.query
                else:
                    scheme = 'https' if getattr(self, '_fixture_tls_tunnel', False) else 'http'
                    authority = (self.headers.get('host') or '').lower()
                    request_path = self.path
                allowed = scheme in ('http', 'https') and authority == owner.target_authority
                row = {'method': self.command, 'scheme': scheme, 'authority': authority,
                       'path': request_path.split('?', 1)[0], 'allowed': allowed}
                length = int(self.headers.get('content-length', '0') or '0')
                body = self.rfile.read(length) if length else b''
                if allowed and row['path'].startswith('/api/'):
                    try:
                        payload = json.loads(body) if body else {}
                        if row['path'].endswith('/turns/stream'):
                            row['request_id'] = payload.get('request_id')
                        if row['path'].endswith('/answers'):
                            row['answer_has_options'] = bool(payload.get('option_ids'))
                            quantity_values = list((payload.get('quantities') or {}).values())
                            row['answer_has_quantities'] = bool(quantity_values)
                            row['answer_quantity_values'] = sorted(value for value in quantity_values
                                                                  if type(value) is int)
                    except (ValueError, TypeError):
                        pass
                self._row(row)
                if not allowed:
                    denied_body = b'external authority denied'
                    self.send_response(403)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.send_header('Content-Length', str(len(denied_body)))
                    self.send_connection_close()
                    try:
                        self.wfile.write(denied_body)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    return

                headers = {key: value for key, value in self.headers.items()
                           if key.lower() not in ('connection', 'proxy-connection', 'host', 'content-length')}
                headers['Host'] = owner.target_authority
                headers['Connection'] = 'close'
                if body:
                    headers['Content-Length'] = str(len(body))
                connection = HTTPConnection('127.0.0.1', owner.target_port, timeout=60)
                try:
                    connection.request(self.command, request_path, body=body or None, headers=headers)
                    upstream = connection.getresponse()
                    self.send_response(upstream.status, upstream.reason)
                    has_body = self.command != 'HEAD' and upstream.status not in (204, 304)
                    for key, value in upstream.getheaders():
                        if key.lower() not in ('connection', 'transfer-encoding', 'content-length', 'server', 'date'):
                            self.send_header(key, value)
                    if has_body:
                        self.send_header('Transfer-Encoding', 'chunked')
                    else:
                        self.send_header('Content-Length', '0')
                    self.send_header('Connection', 'keep-alive')
                    self.end_headers()
                    if has_body:
                        while True:
                            block = upstream.read1(16384)
                            if not block:
                                break
                            self.wfile.write((format(len(block), 'x') + '\r\n').encode('ascii'))
                            self.wfile.write(block + b'\r\n')
                            self.wfile.flush()
                        self.wfile.write(b'0\r\n\r\n')
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    self.close_connection = True
                finally:
                    connection.close()

            do_GET = _forward
            do_POST = _forward
            do_PUT = _forward
            do_PATCH = _forward
            do_DELETE = _forward
            do_OPTIONS = _forward
            do_HEAD = _forward

        owner = self
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, name='fixture-proxy', daemon=True)

    @property
    def port(self):
        return self.server.server_port

    def start(self):
        self.thread.start()

    def snapshot(self):
        with self.lock:
            return [dict(row) for row in self.rows]

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)


class Journey:
    def __init__(self, driver, artifacts: Path):
        self.driver = driver
        self.artifacts = artifacts

    def wait(self, predicate, timeout=15, message='condition not met'):
        return WebDriverWait(self.driver, timeout, poll_frequency=0.1,
                             ignored_exceptions=(Exception,)).until(predicate, message)

    def find(self, by, selector, timeout=10, root=None):
        root = root or self.driver
        return self.wait(lambda _driver: next((item for item in root.find_elements(by, selector)
                                               if item.is_displayed()), False), timeout,
                         'element not found/visible: ' + selector)

    def click(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center',inline:'center'});", element)
        element.click()

    def button(self, name, exact=True, timeout=10, root=None):
        literal = xpath_string(name)
        predicate = f"normalize-space(string(.))={literal} or @aria-label={literal}" if exact else f"contains(normalize-space(string(.)),{literal}) or contains(@aria-label,{literal})"
        path = ('.//' if root is not None else '//') + f"button[{predicate}]"
        return self.find(By.XPATH, path, timeout, root)

    def optional_button(self, name, exact=True):
        literal = xpath_string(name)
        predicate = f"normalize-space(string(.))={literal} or @aria-label={literal}" if exact else f"contains(normalize-space(string(.)),{literal}) or contains(@aria-label,{literal})"
        return next((item for item in self.driver.find_elements(By.XPATH, f"//button[{predicate}]") if item.is_displayed()), None)

    def text(self, value, exact=True, timeout=10):
        literal = xpath_string(value)
        predicate = f"normalize-space(string(.))={literal}" if exact else f"contains(normalize-space(string(.)),{literal})"
        return self.find(By.XPATH, f"//*[self::p or self::span or self::summary or self::h1 or self::h2 or self::h3][{predicate}]", timeout)

    def text_count(self, value, exact=True):
        literal = xpath_string(value)
        predicate = f"normalize-space(string(.))={literal}" if exact else f"contains(normalize-space(string(.)),{literal})"
        return sum(1 for item in self.driver.find_elements(By.XPATH, f"//*[self::p or self::span or self::summary or self::h1 or self::h2 or self::h3][{predicate}]") if item.is_displayed())

    def dialog(self, name, timeout=10):
        return self.find(By.XPATH, f"//*[@role='dialog' and @aria-label={xpath_string(name)}]", timeout)

    def region(self, name, timeout=10):
        return self.find(By.XPATH, f"//*[@role='region' and @aria-label={xpath_string(name)}]", timeout)

    def label(self, name, timeout=10):
        return self.find(By.XPATH, f"//*[@aria-label={xpath_string(name)}]", timeout)

    def placeholder(self, name, timeout=10):
        return self.find(By.XPATH, f"//*[@placeholder={xpath_string(name)}]", timeout)

    def bubble_elements(self, content):
        literal = xpath_string(content)
        return [item for item in self.driver.find_elements(By.XPATH, f"//div[@style and normalize-space(string(.))={literal}]") if item.is_displayed()]

    def api(self, path):
        return self.driver.execute_async_script("""
            const path=arguments[0],done=arguments[arguments.length-1];
            fetch(path,{credentials:'include'}).then(async r=>{
              const body=await r.text();
              let value;try{value=JSON.parse(body)}catch{value={raw:body}}
              if(!r.ok) throw new Error(path+':'+r.status);
              done(value);
            }).catch(e=>done({__error:String(e)}));
        """, path)

    def screenshot(self, name):
        time.sleep(0.25)
        self.driver.save_screenshot(str(self.artifacts / (name + '.png')))

    def send(self, message, role='可可'):
        field = self.placeholder('问问' + role + '吧…')
        field.clear()
        field.send_keys(message, Keys.ENTER)

    def settled(self, timeout=25):
        self.wait(lambda _driver: not any(item.is_displayed() for item in self.driver.find_elements(By.XPATH, "//button[@aria-label='停止本次处理']")), timeout, 'turn did not settle')

    def open_keke(self):
        close = self.driver.find_elements(By.XPATH, "//button[@aria-label='关闭聊天']")
        if close and close[0].is_displayed():
            self.click(close[0])
        goods = self.optional_button('商品')
        if goods:
            self.click(goods)
        ask = self.optional_button('问问可可')
        if ask:
            self.click(ask)
        self.placeholder('问问可可吧…')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--geckodriver', type=Path, required=True)
    parser.add_argument('--firefox', type=Path, required=True)
    parser.add_argument('--artifacts', type=Path, required=True)
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(Path(os.environ['FIXTURE_MANIFEST']).read_text())
    base = urlsplit(manifest['base_url'])
    browser_url = urlsplit(manifest['browser_url'])
    entry_url = manifest['entry_url']
    assert base.scheme == browser_url.scheme == 'http'
    assert base.hostname and ipaddress.ip_address(base.hostname).is_loopback
    assert browser_url.hostname and browser_url.hostname.endswith('.localhost')
    assert base.port == browser_url.port
    assert urlsplit(entry_url).hostname == browser_url.hostname and urlsplit(entry_url).port == browser_url.port
    exact_authority = browser_url.netloc.lower()
    cert_file = args.artifacts / 'fixture-origin-cert.pem'
    key_file = args.artifacts / 'fixture-origin-key.pem'
    subprocess.run(['/usr/bin/openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                    '-keyout', str(key_file), '-out', str(cert_file), '-days', '2',
                    '-subj', '/CN=' + browser_url.hostname,
                    '-addext', 'subjectAltName=DNS:' + browser_url.hostname],
                   check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    key_file.chmod(0o600)

    proxy = ExactFixtureProxy(exact_authority, base.port, cert_file, key_file)
    proxy.start()
    driver = None
    checks = []
    interim_observation = {}
    try:
        options = Options()
        options.binary_location = str(args.firefox.resolve())
        options.add_argument('-headless')
        options.accept_insecure_certs = True
        options.set_preference('network.proxy.type', 1)
        options.set_preference('network.proxy.http', '127.0.0.1')
        options.set_preference('network.proxy.http_port', proxy.port)
        options.set_preference('network.proxy.ssl', '127.0.0.1')
        options.set_preference('network.proxy.ssl_port', proxy.port)
        options.set_preference('network.proxy.no_proxies_on', '')
        options.set_preference('network.proxy.allow_hijacking_localhost', True)
        options.set_preference('network.trr.mode', 5)
        options.set_preference('app.update.enabled', False)
        options.set_preference('browser.shell.checkDefaultBrowser', False)
        options.set_preference('browser.startup.homepage', 'about:blank')
        options.set_preference('toolkit.telemetry.enabled', False)
        options.set_preference('datareporting.healthreport.uploadEnabled', False)
        service = Service(executable_path=str(args.geckodriver.resolve()), log_output=str(args.artifacts / 'geckodriver.log'))
        driver = webdriver.Firefox(service=service, options=options)
        driver.set_window_size(1100, 1000)
        driver.set_page_load_timeout(20)
        driver.set_script_timeout(20)
        page = Journey(driver, args.artifacts)

        # Verify the actual browser HTTP stack is forced through the local deny proxy.
        blocked_before = len([row for row in proxy.snapshot() if not row.get('allowed')])
        try:
            driver.get('http://example.com/')
        except Exception:
            pass
        blocked_rows = [row for row in proxy.snapshot() if not row.get('allowed')]
        assert len(blocked_rows) > blocked_before and blocked_rows[-1]['authority'] == 'example.com', blocked_rows[-3:]
        try:
            driver.get('https://example.com/')
        except Exception:
            pass
        blocked_rows = [row for row in proxy.snapshot() if not row.get('allowed')]
        assert any(row.get('method') == 'CONNECT' and row.get('authority') == 'example.com:443' for row in blocked_rows), blocked_rows[-5:]
        driver.get(entry_url)
        assert driver.current_url == browser_url.geturl() + '/'
        http_security_context = driver.execute_script("return {isSecureContext:window.isSecureContext,cryptoRandomUUID:typeof window.crypto.randomUUID,origin:location.origin}")
        (args.artifacts / 'browser-http-context.json').write_text(json.dumps(http_security_context, indent=2))
        secure_entry_url = entry_url.replace('http://', 'https://', 1)
        driver.get(secure_entry_url)
        secure_origin = 'https://' + browser_url.netloc
        assert driver.current_url == secure_origin + '/'
        security_context = driver.execute_script("return {isSecureContext:window.isSecureContext,cryptoRandomUUID:typeof window.crypto.randomUUID,origin:location.origin}")
        assert security_context['isSecureContext'] and security_context['cryptoRandomUUID'] == 'function', security_context
        page.click(page.button('商品'))
        controls_before_category = driver.execute_script("""
          return [...document.querySelectorAll('button,[role=button]')].filter(el=>{
            const r=el.getBoundingClientRect(),s=getComputedStyle(el);
            return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
          }).map(el=>({tag:el.tagName.toLowerCase(),role:el.getAttribute('role')||'button',
            name:(el.getAttribute('aria-label')||el.innerText||'').trim().replace(/\\s+/g,' '),
            pressed:el.getAttribute('aria-pressed'),disabled:!!el.disabled,
            bounds:(()=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})()}));
        """)
        category_text = page.text('饮料')
        page.click(category_text.find_element(By.XPATH, './ancestor::button[1]'))
        controls_after_category = driver.execute_script("""
          return [...document.querySelectorAll('button,[role=button]')].filter(el=>{
            const r=el.getBoundingClientRect(),s=getComputedStyle(el);
            return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';
          }).map(el=>({tag:el.tagName.toLowerCase(),role:el.getAttribute('role')||'button',
            name:(el.getAttribute('aria-label')||el.innerText||'').trim().replace(/\\s+/g,' '),
            pressed:el.getAttribute('aria-pressed'),disabled:!!el.disabled,
            bounds:(()=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})()}));
        """)
        visible_dom_controls = {'before_category': controls_before_category, 'after_category': controls_after_category}
        (args.artifacts / 'visible-dom-controls.json').write_text(json.dumps(visible_dom_controls, ensure_ascii=False, indent=2))
        (args.artifacts / 'browser-context.json').write_text(json.dumps(security_context, indent=2))

        product = manifest['product']
        page.click(page.button('查看' + product['name'] + '详情'))
        detail = page.dialog('商品详情')
        assert '模拟数据' in detail.text
        assert not page.api('/api/v1/cart')['items']
        page.click(page.button('添加一件到购物车', root=detail))
        cart = page.api('/api/v1/cart')
        assert len(cart['items']) == 1 and cart['items'][0]['quantity'] == 1
        page.screenshot('01-product-detail')
        page.click(page.button('关闭', root=detail))

        page.click(page.button('购物车', exact=False))
        page.click(page.button('模拟结算'))
        checkout = page.dialog('模拟结算')
        assert '不会付款或真实配送' in checkout.text
        page.click(page.button('确认模拟结算'))
        page.wait(lambda _driver: '模拟订单已保存' in page.dialog('模拟结算').text, 10)
        order = next(row for row in page.api('/api/v1/orders')['items'] if row['order_id'] not in manifest['order_ids'])
        snapshot = order['items']; amount = order['total_fen']
        page.click(page.button('查看订单'))
        page.click(page.button('查看订单 ' + order['order_id']))
        page.click(page.button('模拟推进至配送中'))
        page.click(page.button('模拟签收'))
        assert 'delivered' in page.find(By.CSS_SELECTOR, '[data-order-id]').text
        final = page.api('/api/v1/orders/' + order['order_id'])
        assert final['items'] == snapshot and final['total_fen'] == amount
        checks.append('product explicit add, simulated checkout, immutable order snapshot and demo delivery progression')
        page.screenshot('02-order-snapshot')

        page.click(page.button('联系墨墨'))
        page.label('售后类型')
        case = driver.execute_script("return localStorage.getItem('ceres-mercury-case')")
        assert page.api('/api/v1/mercury/sessions/' + case)['order_id'] == order['order_id']
        Select(page.label('售后类型')).select_by_value('quality')
        Select(page.label('退货商品')).select_by_value(product['sku_id'])
        page.label('问题销售包装数').send_keys('1')
        page.placeholder('申请原因').send_keys('受控演示包装破损')
        png = args.artifacts / 'synthetic.png'
        png.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGPgEpEDAABoAD1UCKP3AAAAAElFTkSuQmCC'))
        page.label('质量问题照片').send_keys(str(png.resolve()))
        page.find(By.XPATH, "//*[@alt='待人工核对的照片']", timeout=10)
        page.click(page.button('查看申请提案'))
        page.wait(lambda _driver: '质量问题登记' in page.find(By.CSS_SELECTOR, '[data-proposal-id]').text, 10)
        page.click(page.button('确认提交此模拟申请'))
        summary = page.find(By.XPATH, "//summary[contains(normalize-space(.),'异步人工工单')]", timeout=10)
        page.click(summary)
        page.find(By.XPATH, "//*[@alt='待核对的问题照片']", timeout=10)
        human = page.api('/api/v1/mercury/sessions/' + case + '/human-ticket')
        assert len(human['applications']) == 1 and len(human['photos']) == 1
        checks.append('explicit quality count/photo confirmation and evidence in the corresponding human ticket')
        page.screenshot('03-ticket-evidence')

        selected = page.api('/api/v1/mercury/sessions/' + case)
        page.click(page.button('关闭聊天'))
        page.click(page.button('联系墨墨'))
        page.placeholder('问问墨墨吧…')
        assert page.api('/api/v1/mercury/sessions/' + case)['selection_version'] == selected['selection_version']
        checks.append('same-order contact preserves canonical selection version')

        page.open_keke()
        page.send(manifest['scenarios']['yes'])
        page.button('留在这里', timeout=25)
        before_rejection_streams = len([row for row in proxy.snapshot()
                                        if row.get('path', '').endswith('/turns/stream')])
        page.click(page.button('留在这里'))
        page.click(page.button('墨墨 · 订单售后'))
        page.placeholder('问问墨墨吧…')
        after_rejection_streams = len([row for row in proxy.snapshot()
                                       if row.get('path', '').endswith('/turns/stream')])
        assert after_rejection_streams == before_rejection_streams, {
            'before': before_rejection_streams, 'after': after_rejection_streams}
        checks.append('yes rejection followed by pure Momo role button does not replay the original request')

        page.open_keke()
        page.send(manifest['scenarios']['yes'])
        page.click(page.button('切换并继续原请求', timeout=25))
        page.placeholder('问问墨墨吧…')
        checks.append('controlled positive role decision explicitly enters Momo')

        page.open_keke()
        page.send(manifest['scenarios']['no'])
        page.text('你好，这是受控浏览器演示。', timeout=25)
        page.settled()
        for outcome in ('uncertain', 'error', 'timeout'):
            previous = page.text_count('你好，这是受控浏览器演示。')
            page.send(manifest['scenarios'][outcome])
            page.wait(lambda _driver: page.text_count('你好，这是受控浏览器演示。') == previous + 1, 25)
            page.settled()
        checks.append('no/uncertain/error/timeout preserve the original Coco request')

        page.send(manifest['scenarios']['mixed'])
        page.button('前往墨墨处理', exact=False, timeout=25)
        page.settled()
        page.screenshot('04-mixed-result')
        before_streams = len([row for row in proxy.snapshot() if row.get('path', '').endswith('/turns/stream')])
        page.click(page.button('前往墨墨处理', exact=False))
        page.placeholder('问问墨墨吧…')
        assert len([row for row in proxy.snapshot() if row.get('path', '').endswith('/turns/stream')]) == before_streams
        checks.append('mixed shopping/policy result retains explicit role boundary; role action does not replay')

        page.open_keke()
        sid = driver.execute_script("return sessionStorage.getItem('ceres-langgraph-guide-session-id')")
        assert sid, 'opening Keke did not establish the current Guide session'
        expected_interims = ('我先核对演示商品，再说明下一步。', '我继续核对可展示的商品信息。')
        before_interim = page.api('/api/v1/guide/sessions/' + sid + '?include_messages=1')['messages']
        before_interim_ids = {row['message_id'] for row in before_interim}
        before_interim_bubble_counts = {content: len(page.bubble_elements(content)) for content in expected_interims}
        page.send(manifest['scenarios']['interim'])
        current_user = page.wait(lambda _driver: next((row for row in
            page.api('/api/v1/guide/sessions/' + sid + '?include_messages=1').get('messages', [])
            if row.get('role') == 'user' and row.get('content') == manifest['scenarios']['interim']
            and row.get('message_id') not in before_interim_ids and row.get('request_id')), False), 20,
            'current INTERIM request was not accepted')
        current_request_id = current_user['request_id']
        current_receipt = page.wait(lambda _driver: (lambda value: value if
            value.get('status') in ('completed', 'failed', 'stopped', 'interrupted', 'protected') else False)(
                page.api('/api/v1/guide/sessions/' + sid + '/turns/' + current_request_id)), 25,
            'current INTERIM request did not reach a terminal receipt')
        assert current_receipt['status'] == 'completed', current_receipt
        page.settled()
        history = page.api('/api/v1/guide/sessions/' + sid + '?include_messages=1')['messages']
        ids = [row['message_id'] for row in history]
        assert len(ids) == len(set(ids))
        interim_rows = [row for row in history if row.get('request_id') == current_request_id
                        and row['content'] in expected_interims]
        assert len(interim_rows) == 2 and len({row['message_id'] for row in interim_rows}) == 2, {
            'count': len(interim_rows), 'messages': [{'message_id': row.get('message_id'),
                'request_id': row.get('request_id'), 'content': row.get('content')}
                for row in interim_rows]}
        assert all(row['message_id'] not in before_interim_ids for row in interim_rows), {
            'request_id': current_request_id, 'messages': interim_rows}
        positions = [next(index for index, row in enumerate(history) if row['message_id'] == item['message_id']) for item in interim_rows]
        assert positions == sorted(positions) and positions[-1] < len(history) - 1
        visible = []
        for row in interim_rows:
            bubbles = page.bubble_elements(row['content'])
            assert len(bubbles) == before_interim_bubble_counts[row['content']] + 1, {
                'content': row['content'], 'before': before_interim_bubble_counts[row['content']],
                'after': len(bubbles)}
            bubble = bubbles[-1]
            geometry = driver.execute_script("""
              const el=arguments[0];el.scrollIntoView({block:'center'});
              const r=el.getBoundingClientRect(),s=el.closest('.overflow-y-auto'),v=s?.getBoundingClientRect();
              const top=Math.max(r.top,v?.top??0,0),bottom=Math.min(r.bottom,v?.bottom??innerHeight,innerHeight);
              const left=Math.max(r.left,v?.left??0,0),right=Math.min(r.right,v?.right??innerWidth,innerWidth);
              return {x:r.x,y:r.y,width:r.width,height:r.height,opacity:Number(getComputedStyle(el).opacity),visible_area:Math.max(0,bottom-top)*Math.max(0,right-left),scroll_top:s?.scrollTop};
            """, bubble)
            assert geometry['width'] > 0 and geometry['height'] > 0 and geometry['opacity'] >= .9 and geometry['visible_area'] > 0, geometry
            visible.append({'message_id': row['message_id'], 'content': row['content'], 'geometry': geometry})
        interim_observation['completed_turn_visible'] = visible
        page.screenshot('05-interim-after-completion-visible')
        driver.refresh()
        page.placeholder('问问可可吧…')
        page.settled()
        restored = page.api('/api/v1/guide/sessions/' + sid + '?include_messages=1')['messages']
        assert [row['message_id'] for row in restored] == ids
        for row in interim_rows:
            assert len(page.bubble_elements(row['content'])) == before_interim_bubble_counts[row['content']] + 1
        page.screenshot('06-interim-restored')
        checks.append('current-run interim IDs were unique; the repeated mixed-turn text remained separate, visible bubbles, and refresh restored identical stable IDs')

        # Capture the current history/count before sending. The slow scenario
        # reuses the first interim text, so only a new request_id + message_id
        # proves the visible bubble belongs to this still-running turn.
        before = page.api('/api/v1/guide/sessions/' + sid + '?include_messages=1')['messages']
        before_ids = {row['message_id'] for row in before}
        before_count = len(page.bubble_elements('我先核对演示商品，再说明下一步。'))
        before_stream_ids = {row['request_id'] for row in proxy.snapshot()
                             if row.get('path', '').endswith('/turns/stream') and row.get('request_id')}
        page.send(manifest['scenarios']['slow'])
        stream_row = None
        for _ in range(100):
            streams = [row for row in proxy.snapshot()
                       if row.get('path', '').endswith('/turns/stream') and row.get('request_id')
                       and row['request_id'] not in before_stream_ids]
            if streams:
                stream_row = streams[0]
                break
            time.sleep(.03)
        assert stream_row is not None, 'slow stream request was not observed by the proxy'
        request_id = stream_row['request_id']
        new_interim = None
        receipt = None
        event_snapshot = None
        for _ in range(130):
            receipt = page.api('/api/v1/guide/sessions/' + sid + '/turns/' + request_id)
            if not receipt.get('__error') and receipt.get('run_id'):
                event_snapshot = page.api('/api/v1/guide/sessions/' + sid + '/runs/' + receipt['run_id'] + '/events')
                current = page.api('/api/v1/guide/sessions/' + sid + '?include_messages=1')['messages']
                candidates = [row for row in current if row['request_id'] == request_id and row['message_id'] not in before_ids and row['content'] == '我先核对演示商品，再说明下一步。']
                if candidates:
                    new_interim = candidates[-1]
                    break
            time.sleep(.05)
        assert new_interim is not None, 'the new slow request did not publish its own interim message'
        assert receipt and receipt['status'] == 'running', receipt
        assert event_snapshot and event_snapshot['status'] == 'running'
        assert not any(row['type'] in ('turn.completed', 'turn.stopped', 'error') for row in event_snapshot['events']), event_snapshot
        bubbles = page.bubble_elements('我先核对演示商品，再说明下一步。')
        assert len(bubbles) > before_count, {'before': before_count, 'after': len(bubbles)}
        bubble = bubbles[-1]
        geometry = driver.execute_script("""
          const el=arguments[0];el.scrollIntoView({block:'center'});
          const r=el.getBoundingClientRect(),s=el.closest('.overflow-y-auto'),v=s?.getBoundingClientRect();
          const top=Math.max(r.top,v?.top??0,0),bottom=Math.min(r.bottom,v?.bottom??innerHeight,innerHeight);
          const left=Math.max(r.left,v?.left??0,0),right=Math.min(r.right,v?.right??innerWidth,innerWidth);
          return {x:r.x,y:r.y,width:r.width,height:r.height,opacity:Number(getComputedStyle(el).opacity),visible_area:Math.max(0,bottom-top)*Math.max(0,right-left),scroll_top:s?.scrollTop};
        """, bubble)
        assert geometry['width'] > 0 and geometry['height'] > 0 and geometry['opacity'] >= .9 and geometry['visible_area'] > 0, geometry
        assert any(item.is_displayed() for item in driver.find_elements(By.XPATH, "//button[@aria-label='停止本次处理']"))
        interim_observation['live_turn'] = {'request_id': request_id, 'run_id': receipt['run_id'],
            'message_id': new_interim['message_id'], 'receipt_status_before_stop': receipt['status'],
            'event_status_before_stop': event_snapshot['status'], 'terminal_events_before_stop': 0,
            'visible_geometry_before_stop': geometry}
        page.screenshot('07-interim-before-stop-visible')
        page.click(page.button('停止本次处理'))

        terminal_receipt = None
        for _ in range(180):
            terminal_receipt = page.api('/api/v1/guide/sessions/' + sid + '/turns/' + request_id)
            if terminal_receipt.get('status') in ('stopped', 'completed', 'failed', 'interrupted', 'protected'):
                break
            time.sleep(.1)
        assert terminal_receipt and terminal_receipt.get('status') == 'stopped', terminal_receipt
        terminal_events = page.api('/api/v1/guide/sessions/' + sid + '/runs/' + terminal_receipt['run_id'] + '/events')
        assert terminal_events['status'] == 'stopped' and terminal_events['events'][-1]['type'] == 'turn.stopped'
        after_stop = page.api('/api/v1/guide/sessions/' + sid + '?include_messages=1')['messages']
        stopped_ids = [row['message_id'] for row in after_stop if row['request_id'] == request_id]
        time.sleep(.3)
        after_quiet = page.api('/api/v1/guide/sessions/' + sid + '?include_messages=1')['messages']
        assert [row['message_id'] for row in after_quiet if row['request_id'] == request_id] == stopped_ids
        interim_observation['live_turn'].update({'terminal_receipt_status': terminal_receipt['status'],
            'terminal_event': terminal_events['events'][-1]['type'], 'messages_stable_after_stop': True})
        checks.append('new interim bubble was visible while this request receipt was running; stop persisted stopped receipt/event with no subsequent message publication')
        page.screenshot('08-stopped')

        page.send(manifest['scenarios']['typed'])
        category = page.label('想看哪类饮品？', timeout=20)
        page.click(category.find_elements(By.TAG_NAME, 'button')[0])
        choices = page.label('请选择商品和销售包装数量，选定后再核对清单。', timeout=20)
        page.wait(lambda _driver: bool(choices.find_elements(By.XPATH, ".//input[@type='checkbox']")), 20)
        choice = choices.find_elements(By.XPATH, ".//input[@type='checkbox']")[0]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", choice)
        if not choice.is_selected():
            choice.click()
        quantity = choices.find_elements(By.XPATH, ".//input[@type='number']")[0]
        quantity.clear(); quantity.send_keys('1')
        submit_selection = page.button('生成采购清单', root=choices)
        assert submit_selection.is_enabled()
        page.click(submit_selection)
        page.wait(lambda _driver: '已回答' in page.label('请选择商品和销售包装数量，选定后再核对清单。').text, 15)
        answer_rows = [row for row in proxy.snapshot() if '/questions/' in row.get('path', '') and row.get('path', '').endswith('/answers')]
        assert len(answer_rows) >= 2 and all(row.get('answer_has_options') for row in answer_rows)
        assert any(row.get('answer_quantity_values') == [1] for row in answer_rows), answer_rows
        page.text('采购清单', timeout=20)
        typed_snapshot = page.api('/api/v1/guide/sessions/' + sid)
        assert typed_snapshot.get('plan') and len(typed_snapshot['plan']['items']) == 1, typed_snapshot
        assert typed_snapshot['plan']['items'][0]['quantity'] == 1, typed_snapshot['plan']['items']
        assert not page.api('/api/v1/cart')['items']
        checks.append('native typed category and explicit product/quantity selection creates a plan without cart write')
        page.screenshot('09-typed-plan')

        rows = proxy.snapshot()
        blocked = [row for row in rows if not row.get('allowed')]
        assert any(row.get('authority') == 'example.com' for row in blocked)
        assert any(row.get('method') == 'CONNECT' and row.get('authority') == 'example.com:443' for row in blocked)
        assert all(row.get('allowed') for row in rows if row.get('authority') == exact_authority)
        print(json.dumps({'ok': True, 'level': 'real-system-Firefox-controlled-loopback-backend',
            'firefox_version': driver.capabilities.get('browserVersion'),
            'geckodriver_version': '0.37.1', 'fresh_profile': True,
            'exact_fixture_authority': exact_authority, 'http_origin_context': http_security_context,
            'https_origin_context': security_context,
            'checks': checks,
            'interim': interim_observation, 'browser_proxy_requests': len(rows),
            'blocked_external_authorities': sorted({row.get('authority') for row in blocked}),
            'boundaries': manifest['boundaries']}, ensure_ascii=False))
    except Exception:
        if driver is not None:
            try:
                driver.save_screenshot(str(args.artifacts / 'failure.png'))
            except Exception:
                pass
            try:
                sid = driver.execute_script("return sessionStorage.getItem('ceres-langgraph-guide-session-id')")
                if sid:
                    history = page.api('/api/v1/guide/sessions/' + sid + '?include_messages=1')
                    messages = history.get('messages', [])
                    last_request = next((row.get('request_id') for row in reversed(messages)
                                         if row.get('request_id')), None)
                    receipt = page.api('/api/v1/guide/sessions/' + sid + '/turns/' + last_request) if last_request else {}
                    events = page.api('/api/v1/guide/sessions/' + sid + '/runs/' + receipt['run_id'] + '/events') \
                        if receipt.get('run_id') else {}
                    safe_events = []
                    for row in events.get('events', []):
                        payload = row.get('payload') or {}
                        diagnostic = payload.get('diagnostic') or {}
                        safe_events.append({'type': row.get('type'), 'code': payload.get('code'),
                            **({'message_id': payload.get('message_id'),
                                'content': payload.get('content')}
                               if row.get('type') == 'message.interim' else {}),
                            'diagnostic': {key: diagnostic.get(key) for key in
                                           ('kind', 'code', 'fingerprint', 'transport_phase',
                                            'transport_error_class', 'transport_error_code',
                                            'upstream_http_status') if key in diagnostic}})
                    (args.artifacts / 'failure-runtime-diagnostic.json').write_text(json.dumps({
                        'message_count': len(messages), 'last_request_id': last_request,
                        'receipt_status': receipt.get('status'), 'receipt_run_id': receipt.get('run_id'),
                        'event_status': events.get('status'), 'events': safe_events,
                        'current_request_interims': [{'message_id': row.get('message_id'),
                            'kind': row.get('kind'), 'content': row.get('content')}
                            for row in messages if row.get('request_id') == last_request
                            and row.get('role') == 'assistant' and row.get('kind') == 'interim'],
                        'expected_interims': [{'message_id': row.get('message_id'),
                            'request_id': row.get('request_id'), 'content': row.get('content')}
                            for row in messages if row.get('content') in
                            ('我先核对演示商品，再说明下一步。', '我继续核对可展示的商品信息。')]}, indent=2))
            except Exception as diagnostic_error:
                (args.artifacts / 'failure-runtime-diagnostic.json').write_text(json.dumps({
                    'capture_error_class': type(diagnostic_error).__name__}, indent=2))
        raise
    finally:
        if driver is not None:
            capabilities = driver.capabilities
            try:
                driver.quit()
            finally:
                (args.artifacts / 'browser-capabilities.json').write_text(json.dumps({
                    'browserName': capabilities.get('browserName'),
                    'browserVersion': capabilities.get('browserVersion'),
                    'platformName': capabilities.get('platformName'),
                    'moz:profile': capabilities.get('moz:profile'),
                    'geckodriverVersion': '0.37.1'}, indent=2))
        proxy.close()
        rows = proxy.snapshot()
        (args.artifacts / 'proxy-requests.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2))
        (args.artifacts / 'proxy-blocks.json').write_text(json.dumps([row for row in rows if not row.get('allowed')], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
