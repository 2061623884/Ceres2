"""Controlled public Ceres SystemOne transport; does not claim a live Kev sample."""
import json
from types import SimpleNamespace
import httpx
import pytest
from app.services import kev_provider


def test_joint_route_uses_one_systemone_choice_question(monkeypatch):
    calls = []
    def transport(request):
        calls.append(request)
        return httpx.Response(200, json={'model':'kev-latest','answers':{'service':{
            'type':'choice','choice':'momo','probabilities':{key:(1.0 if key=='momo' else 0.0) for key in kev_provider.CRITERIA}}}})
    monkeypatch.setattr(kev_provider, 'get_settings', lambda:SimpleNamespace(kev_base_url='http://fixture.invalid'))
    fixture_client = httpx.Client(transport=httpx.MockTransport(transport))
    monkeypatch.setattr(kev_provider, 'client', lambda:fixture_client)
    choice, raw = kev_provider.judge({'current_role':'keke','message':'看一下这笔订单','selected_object':None,'recent_dialogue':[]})
    assert choice == 'momo'
    assert len(calls) == 1
    assert calls[0].url.path == '/v1/systemone'
    payload = json.loads(calls[0].content)
    assert payload['model'] == 'kev-latest'
    assert list(payload['questions']) == ['service']
    assert payload['questions']['service']['type'] == 'choice'
    assert set(payload['questions']['service']['criteria']) == set(kev_provider.CRITERIA)
    assert not any(key.startswith('momo_') for key in kev_provider.CRITERIA)
    fixture_client.close()


def test_invalid_external_contract_is_visible_failure_without_fallback(monkeypatch):
    calls = []
    def transport(request):
        calls.append(request)
        return httpx.Response(200, json={'choices':[{'text':'momo'}]})
    monkeypatch.setattr(kev_provider,'get_settings',lambda:SimpleNamespace(kev_base_url='http://fixture.invalid'))
    fixture_client = httpx.Client(transport=httpx.MockTransport(transport))
    monkeypatch.setattr(kev_provider,'client',lambda:fixture_client)
    with pytest.raises(kev_provider.KevUnavailable):
        kev_provider.judge({'current_role':'keke','message':'原请求'})
    assert len(calls) == 1
    fixture_client.close()


def test_old_three_choice_response_fails_explicitly_without_label_guessing(monkeypatch):
    calls = []
    def transport(request):
        calls.append(request)
        return httpx.Response(200,json={'model':'kev-latest','answers':{'service':{'type':'choice','choice':'stay_current','probabilities':{'stay_current':1.0,'suggest_switch':0.0,'clarify':0.0}}}})
    monkeypatch.setattr(kev_provider,'get_settings',lambda:SimpleNamespace(kev_base_url='http://fixture.invalid'))
    with httpx.Client(transport=httpx.MockTransport(transport)) as fixture_client:
        monkeypatch.setattr(kev_provider,'client',lambda:fixture_client)
        with pytest.raises(kev_provider.KevUnavailable):
            kev_provider.judge({'current_role':'momo','message':'回购物并买零食'})
    assert len(calls) == 1
