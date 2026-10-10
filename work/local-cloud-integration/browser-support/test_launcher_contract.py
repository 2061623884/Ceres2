"""Public CLI safety contract; only the dedicated Tester executes these tests."""
import subprocess
import sys
from pathlib import Path

LAUNCHER = Path(__file__).with_name('launch_browser_fixture.py')


def test_existing_project_dotenv_is_refused_before_any_application_import(tmp_path):
    source = tmp_path/'source'
    source.mkdir()
    (source/'.env').write_text('OPENAI_API_KEY=synthetic-secret-must-not-be-read\n')
    result = subprocess.run([sys.executable,str(LAUNCHER),'--source',str(source),
        '--frontend-dist',str(tmp_path/'dist'),'--',sys.executable,'-c','raise SystemExit(77)'],
        text=True,capture_output=True,timeout=5)
    assert result.returncode == 2
    assert 'FIXTURE_REFUSES_PROJECT_DOTENV' in result.stderr
    assert 'synthetic-secret-must-not-be-read' not in result.stdout+result.stderr


import json
import urllib.request
import pytest


@pytest.mark.parametrize('scenario',['mixed','expression'])
def test_controlled_provider_accepts_actual_sdk_text_block_envelopes(scenario):
    from fixture_backend import provider_server
    provider=provider_server({'sku_id':'synthetic-sku'})
    if scenario=='mixed':
        messages=[{'role':'system','content':'Controlled primary Pi'},
            {'role':'user','content':[{'type':'text','text':'CERES_POLICY_EVIDENCE\n'+json.dumps({'policy_ref':'policy-controlled'})}]},
            {'role':'user','content':[{'type':'text','text':'[BROWSER:MIXED] synthetic mixed scenario'}]},
            {'role':'tool','content':json.dumps({'guide_request':True,'kind':'new_goal'})},
            {'role':'tool','content':json.dumps({'products':[{'ref':'product-controlled'}]})}]
        tools=[{'type':'function','function':{'name':'finish_response'}}]
    else:
        messages=[{'role':'system','content':'Controlled expression-only request'},
            {'role':'user','content':[{'type':'text','text':json.dumps({'facts':{'result':'synthetic fact'}})}]}]
        tools=[]
    body={'model':'controlled','stream':True,'messages':messages,'tools':tools}
    try:
        request=urllib.request.Request(f'http://127.0.0.1:{provider.server_port}/v1/chat/completions',
            data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=3) as response:
            rows=[json.loads(line[6:]) for line in response.read().decode().splitlines() if line.startswith('data: ') and line!='data: [DONE]']
        delta=rows[0]['choices'][0]['delta']
        if scenario=='mixed':
            result=json.loads(delta['tool_calls'][0]['function']['arguments'])
            assert result['policy_ref']=='policy-controlled' and result['product_refs']==['product-controlled']
        else:
            assert json.loads(delta['content'])['fact_ref']=='result'
    finally:
        provider.shutdown();provider.server_close()


def test_cli_reaps_owned_term_resistant_descendant_after_leader_exit(tmp_path):
    """Exercise the public launcher, not its private stop helper."""
    import os
    import signal
    import time
    source=Path(os.environ['CERES_BROWSER_TEST_SOURCE'])
    frontend=Path(os.environ['CERES_BROWSER_TEST_DIST'])
    identity=tmp_path/'owned-descendant.json'
    program=r'''
import json,os,signal,sys,time
from pathlib import Path
read_fd,write_fd=os.pipe()
pid=os.fork()
if pid==0:
    os.close(read_fd)
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    null=os.open(os.devnull,os.O_RDWR)
    for descriptor in (0,1,2):
        os.dup2(null,descriptor)
    os.close(null)
    Path(sys.argv[1]).write_text(json.dumps({'pid':os.getpid(),'pgid':os.getpgrp()}))
    os.write(write_fd,b'R');os.close(write_fd)
    while True:
        time.sleep(.1)
os.close(write_fd)
assert os.read(read_fd,1)==b'R'
os.close(read_fd)
os._exit(0)
'''
    owned=None
    try:
        result=subprocess.run([sys.executable,str(LAUNCHER),'--source',str(source),
            '--frontend-dist',str(frontend),'--artifacts',str(tmp_path/'evidence'),'--lifetime','30',
            '--',sys.executable,'-c',program,str(identity)],text=True,capture_output=True,timeout=50)
        owned=json.loads(identity.read_text())
        lifecycle=next(json.loads(line) for line in reversed(result.stdout.splitlines()) if '"fixture_stopped"' in line)
        assert result.returncode==0,(result.stdout,result.stderr)
        assert lifecycle['fixture_stopped'] is True,lifecycle
        try:
            os.kill(owned['pid'],0)
        except ProcessLookupError:
            alive=False
        else:
            alive=True
        assert not alive,'Launcher reported stopped while its known TERM-resistant child still exists'
    finally:
        # Repair only this test's exactly recorded owned group after expected RED.
        if owned is None and identity.exists():
            owned=json.loads(identity.read_text())
        if owned:
            try:
                if os.getpgid(owned['pid'])==owned['pgid']:
                    os.killpg(owned['pgid'],signal.SIGKILL)
            except ProcessLookupError:
                pass
