"""Public mutation marker distinguishes memory reads from committed writes."""
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn
from test_memory_public import memory_hook


def test_only_committed_memory_writes_set_mutation_flag(pi_client):
    client,requests=pi_client
    requests.answer_hook=memory_hook({'action':'save','category':'user','domain':'shopping',
        'key':'drink','content':'可乐选无糖','source_quote':'记住可乐选无糖'})
    saved=turn(client,'记住可乐选无糖','save-flag')[-1]['payload']
    assert saved['committed'] is True
    record=saved['action_results'][0]['records'][0]
    requests.answer_hook=memory_hook({'action':'list'})
    listed=turn(client,'查看记忆','list-flag')[-1]['payload']
    assert listed['committed'] is False
    assert listed['action_results'][0]['records'][0]['memory_id']==record['memory_id']
    requests.answer_hook=memory_hook({'action':'update','memory_id':record['memory_id'],'expected_revision':1,
        'content':'可乐选小瓶','source_quote':'更正为可乐选小瓶'})
    assert turn(client,'更正为可乐选小瓶','update-flag')[-1]['payload']['committed'] is True
    requests.answer_hook=memory_hook({'action':'delete','memory_id':record['memory_id'],'expected_revision':2,
        'source_quote':'删除可乐偏好'})
    assert turn(client,'删除可乐偏好','delete-flag')[-1]['payload']['committed'] is True
    assert client.get('/api/v1/cart').json()['items']==[]
