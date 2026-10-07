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
