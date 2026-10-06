"""TASK07 supply safety and uncertainty public regressions."""
from sqlalchemy import update,delete
from sqlalchemy.orm import Session
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE,command
from test_dish_public import dish_seed,prepare_dish,dish_hook
from test_guide_semantics import turn
from test_supply_public import supply_revision
from app.models.store import Offer
from app.models.catalog import CatalogProduct


def test_partial_low_stock_reports_uncovered_amount_instead_of_old_remainder(pi_client):
    client,requests=pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=1))
        db.commit()
    command(client,'new_goal',goal='八人份番茄炒蛋')
    state=prepare_dish(client,requests,people=8)
    chosen=supply_revision(client,state,'partial-one-six','choose_partial')
    assert chosen.status_code==200,chosen.text
    egg=next(row for row in chosen.json()['items'] if row['ingredient_id']=='egg')
    assert (egg['quantity'],egg['requirement']['quantity'],egg['leftover_quantity'])==(1,12,-6)
    assert chosen.json()['plan_kind']=='partial_purchase'
    assert client.get('/api/v1/cart').json()['items']==[]


def test_unknown_package_quantity_and_missing_pantry_are_not_service_failure(pi_client):
    client,requests=pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(CatalogProduct).where(CatalogProduct.sku_id.in_(['egg-6','egg-10'])).values(spec_quantity=None))
        db.execute(delete(Offer).where(Offer.sku_id=='salt-500'))
        db.execute(delete(CatalogProduct).where(CatalogProduct.sku_id=='salt-500'))
        db.commit()
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests)
    gap=next(g for g in state['plan']['gaps'] if g['ingredient_id']=='egg')
    assert gap['kind']=='spec_unknown'
    assert gap['unknown_attribute']=='spec'
    assert gap['requested_packs'] is None
    assert state['plan']['can_confirm'] is False
    assert client.get('/api/v1/cart').json()['items']==[]


def test_catalog_query_failure_is_error_not_out_of_stock(pi_client,monkeypatch):
    from app.services.dish_service import DishService
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    requests.answer_hook=dish_hook()
    def fail(*args):
        raise RuntimeError('isolated catalog query unavailable')
    monkeypatch.setattr(DishService,'candidates',fail)
    events=turn(client,'番茄炒蛋','broken-supply-query')
    assert events[-1]['type']=='error',events
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items']==[]


def test_alternatives_respect_whole_task_budget_and_exclusions(pi_client):
    client,requests=pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='egg-6').values(available_qty=0))
        db.commit()
    command(client,'new_goal',goal='番茄炒蛋，预算十五元',conditions={'budget_fen':1500})
    state=prepare_dish(client,requests)
    gap=next(g for g in state['plan']['gaps'] if g['ingredient_id']=='egg')
    assert gap['alternatives']==[], '1900-fen whole plan cannot fit 1500-fen task budget'
    command(client,'amend',conditions={'budget_fen':3000,'exclusions':['egg-10']})
    state=prepare_dish(client,requests,request_id='exclude-alternative')
    gap=next(g for g in state['plan']['gaps'] if g['ingredient_id']=='egg')
    assert gap['alternatives']==[], 'Explicitly excluded SKU is not a legal alternative'


def test_existing_cart_quantity_is_subtracted_from_available_sale_packs(pi_client):
    from test_multidish_public import confirm_body
    from test_dish_public import revise_dish
    client,requests=pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='egg-6').values(available_qty=1))
        db.commit()
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests)
    url='/api/v1/guide/tasks/'+state['task_id']
    added=client.post(url+'/items/egg-6/add',json=confirm_body(state,[{'sku_id':'egg-6','quantity':1}]),headers={'Idempotency-Key':'one-reserved-egg-pack'})
    assert added.status_code==200,added.text
    state=client.get(BASE).json()
    changed=revise_dish(client,state,'eight-with-stock-in-cart',people=8)
    assert changed.status_code==200,changed.text
    assert changed.json()['plan_kind']=='supply_preview'
    gap=next(g for g in changed.json()['gaps'] if g['ingredient_id']=='egg')
    assert (gap['requested_packs'],gap['available_packs'],gap['shortfall_packs'])==(1,0,1)
    assert {row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']}=={'egg-6':1}


def test_changed_supply_requires_refresh_display_and_new_confirmation(pi_client):
    from test_multidish_public import confirm_body
    from test_dish_public import revise_dish
    client,requests=pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=0))
        db.commit()
    command(client,'new_goal',goal='番茄炒蛋')
    preview=prepare_dish(client,requests)
    chosen=supply_revision(client,preview,'price-partial','choose_partial')
    assert chosen.status_code==200,chosen.text
    state=client.get(BASE).json()
    old=confirm_body(state)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='tomato-500').values(price_fen=700,offer_version=2))
        db.commit()
    url='/api/v1/guide/tasks/'+state['task_id']
    blocked=client.post(url+'/confirm',json=old,headers={'Idempotency-Key':'old-partial-price'})
    assert blocked.status_code==409,blocked.text
    assert client.get('/api/v1/cart').json()['items']==[]
    refreshed=revise_dish(client,state,'refresh-same-people',people=2)
    assert refreshed.status_code==200,refreshed.text
    fresh=client.get(BASE).json()
    assert fresh['plan']['plan_kind']=='supply_preview'
    assert next(r for r in fresh['plan']['items'] if r['ingredient_id']=='tomato')['unit_price_fen']==700
    chosen=supply_revision(client,fresh,'new-price-partial','choose_partial')
    assert chosen.status_code==200,chosen.text
    fresh=client.get(BASE).json()
    result=client.post(url+'/confirm',json=confirm_body(fresh),headers={'Idempotency-Key':'new-price-confirm'})
    assert result.status_code==200,result.text
    assert client.get('/api/v1/cart').json()['total_price_fen']==700
    from app.core.database import init_db
    before=client.get(BASE).json()['plan']
    init_db(requests.engine);init_db(requests.engine)
    assert client.get(BASE).json()['plan']==before
    assert client.post(url+'/confirm',json=confirm_body(fresh),headers={'Idempotency-Key':'new-price-confirm'}).json()==result.json()


def test_alternative_merges_existing_same_sku_before_pack_rounding(pi_client):
    from test_multidish_public import append_dish,confirm_body
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    prepare_dish(client,requests,selections={'egg':'egg-6'})
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='egg-6').values(available_qty=0))
        db.commit()
    state=append_dish(client,requests,selections={'egg':'egg-10'})
    gap=next(g for g in state['plan']['gaps'] if g['sku_id']=='egg-6')
    chosen=supply_revision(client,state,'merge-compatible-alternative','choose_alternative',gap_id=gap['gap_id'],alternative_index=0)
    assert chosen.status_code==200,chosen.text
    eggs=[row for row in chosen.json()['items'] if row['ingredient_id']=='egg']
    assert len(eggs)==1
    assert (eggs[0]['sku_id'],eggs[0]['quantity'],eggs[0]['requirement']['quantity'],eggs[0]['leftover_quantity'])==('egg-10',1,6,4)
    assert len(eggs[0]['contributions'])==2
    state=client.get(BASE).json()
    result=client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=confirm_body(state),headers={'Idempotency-Key':'merged-alternative-confirm'})
    assert result.status_code==200,result.text
    assert {r['sku_id']:r['quantity'] for r in client.get('/api/v1/cart').json()['items']}=={'egg-10':1,'tomato-500':2}


def test_previously_chosen_spec_quantity_becoming_unknown_is_preview(pi_client):
    from test_dish_public import revise_dish
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests,selections={'egg':'egg-6'})
    with Session(requests.engine) as db:
        db.execute(update(CatalogProduct).where(CatalogProduct.sku_id=='egg-6').values(spec_quantity=None))
        db.commit()
    refreshed=revise_dish(client,state,'unknown-selected-package',people=2)
    assert refreshed.status_code==200,refreshed.text
    gap=next(g for g in refreshed.json()['gaps'] if g['ingredient_id']=='egg')
    assert (gap['kind'],gap['sku_id'],gap['requested_packs'])==('spec_unknown','egg-6',None)
    assert refreshed.json()['plan_kind']=='supply_preview'


def test_alternative_budget_uses_merged_entire_plan_not_duplicate_pack_cost(pi_client):
    from test_multidish_public import append_dish
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='两道番茄炒蛋，预算三十五元',conditions={'budget_fen':3500})
    prepare_dish(client,requests,selections={'egg':'egg-6'})
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='egg-6').values(available_qty=0))
        db.commit()
    state=append_dish(client,requests,selections={'egg':'egg-10'})
    gap=next(g for g in state['plan']['gaps'] if g['sku_id']=='egg-6')
    assert gap['alternatives'], 'Combined 6 eggs need one 10-pack: whole plan 2500, not duplicated 3800'
    chosen=supply_revision(client,state,'budget-merged-alternative','choose_alternative',gap_id=gap['gap_id'],alternative_index=0)
    assert chosen.status_code==200,chosen.text
    assert chosen.json()['selected_total_fen']==2500
    assert client.get('/api/v1/cart').json()['items']==[]


def test_replacing_one_mixed_gap_preserves_untouched_group_allocation(pi_client):
    from test_dish_public import revise_dish
    client,requests=pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=1))
        db.commit()
    command(client,'new_goal',goal='八人份番茄炒蛋')
    state=prepare_dish(client,requests,people=8)
    gap=next(g for g in state['plan']['gaps'] if g['ingredient_id']=='egg')
    index=next(i for i,o in enumerate(gap['alternatives']) if len(o['items'])==2)
    assert supply_revision(client,state,'initial-mixed-shares','choose_alternative',gap_id=gap['gap_id'],alternative_index=index).status_code==200
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='egg-6').values(available_qty=3))
        db.commit()
    state=client.get(BASE).json()
    assert revise_dish(client,state,'sixteen-mixed-shares',people=16).status_code==200
    state=client.get(BASE).json()
    gap=next(g for g in state['plan']['gaps'] if g['sku_id']=='egg-10')
    index=next(i for i,o in enumerate(gap['alternatives']) if len(o['items'])==2)
    selected=supply_revision(client,state,'replace-only-ten-gap','choose_alternative',gap_id=gap['gap_id'],alternative_index=index)
    assert selected.status_code==200,selected.text
    expected={r['sku_id']:r['requirement']['quantity'] for r in selected.json()['items'] if r['ingredient_id']=='egg'}
    assert expected=={'egg-10':10,'egg-6':14}
    state=client.get(BASE).json()
    repeated=revise_dish(client,state,'repeat-sixteen-same-shares',people=16)
    assert repeated.status_code==200,repeated.text
    actual={r['sku_id']:r['requirement']['quantity'] for r in repeated.json()['items'] if r['ingredient_id']=='egg'}
    assert actual==expected
    assert repeated.json()['plan_kind']=='full_plan'
