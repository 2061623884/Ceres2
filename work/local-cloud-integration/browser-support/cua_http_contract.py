"""Tester-only HTTP contract before official cloud-browser UI use."""
from http.client import HTTPConnection
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

manifest=json.loads(Path(os.environ['FIXTURE_MANIFEST']).read_text())
origin=urlsplit(os.environ['BROWSER_BASE_URL'])
assert origin.scheme=='http' and origin.hostname=='127.0.0.1'
connection=HTTPConnection(origin.hostname,origin.port,timeout=5)
# Negative Host cases also run against the previous helper to prove RED.
for host in (origin.netloc,'localhost:'+str(origin.port),'ceres-fixture-other.localhost:'+str(origin.port)):
    connection.request('GET','/__fixture__/start',headers={'Host':host})
    denied=connection.getresponse();denied.read()
    assert denied.status==403,('bootstrap must refuse any non-owned Host',host,denied.status)
    assert denied.getheader('Set-Cookie') is None
browser=urlsplit(manifest['browser_url'])
assert browser.hostname.startswith('ceres-fixture-') and browser.hostname.endswith('.localhost')
assert browser.hostname not in ('localhost','127.0.0.1') and browser.port==origin.port
for path in ('/__fixture__/start','/__fixture__/start?owner=unowned&next=https://external.invalid/'):
    connection.request('GET',path,headers={'Host':browser.netloc})
    response=connection.getresponse();response.read()
    assert response.status==303,('fixture start must redirect only after setting the synthetic identity',response.status)
    assert response.getheader('Location')=='/'
    cookie=SimpleCookie();cookie.load(response.getheader('Set-Cookie'))
    assert cookie['sg_owner_id'].value==manifest['owner_id']
    assert cookie['sg_owner_id']['httponly'] and cookie['sg_owner_id']['samesite']=='lax'
    assert not cookie['sg_owner_id']['domain']
    csp=response.getheader('Content-Security-Policy')
    assert "connect-src 'self'" in csp and "script-src 'self'" in csp
    assert 'img-src \'self\' data: blob:' in csp and "object-src 'none'" in csp
    assert 'unsafe-eval' not in csp and '*' not in csp
connection.request('GET','/health')
response=connection.getresponse();response.read()
assert response.status==200 and "connect-src 'self'" in response.getheader('Content-Security-Policy')
connection.close()
print(json.dumps({'cua_bootstrap_http_contract':'passed','arbitrary_identity_or_redirect':False,'browser_ui_acceptance':False}),flush=True)
