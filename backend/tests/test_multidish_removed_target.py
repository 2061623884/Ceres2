"""A removed stable target cannot be resurrected by a stale update proposal."""
import json
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_dish_public import dish_seed, prepare_dish, dish_hook
from test_multidish_public import group_revision


def test_removed_last_group_is_not_recreated_by_its_old_update_reference(pi_client):
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests)
    group_id=state['plan']['groups'][0]['group_id']
    removed=group_revision(client,state,'remove-last','group_remove',group_id)
    assert removed.status_code==200,removed.text
    empty=client.get(BASE).json()
    assert empty['plan']['groups']==[] and empty['plan']['items']==[]
    assert empty['plan']['can_confirm'] is False
    base_hook=dish_hook(people=3)
    def stale_update(body):
        delta,reason=base_hook(body)
        for call in delta.get('tool_calls',[]):
            if call['function']['name']=='propose_dish':
                args=json.loads(call['function']['arguments'])
                args.update(operation='update',group_id=group_id)
                call['function']['arguments']=json.dumps(args)
        return delta,reason
    requests.answer_hook=stale_update
    events=turn(client,'把刚才那组人数改成三人','removed-update')
    assert events[-1]['type']=='error',events
    assert events[-1]['payload']['code']=='DISH_GROUP_UNKNOWN',events
    assert client.get(BASE).json()['plan']==empty['plan']
    assert client.get('/api/v1/cart').json()['items']==[]
