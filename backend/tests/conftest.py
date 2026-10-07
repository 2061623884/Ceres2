"""Controlled pytest defaults, installed before collection imports the app.

Applies to direct pytest and capture.py -> pytest, not arbitrary captured scripts.
Individual fixtures can still select their own loopback model server and database.
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory

_runtime = TemporaryDirectory(prefix='ceres-controlled-tests-')
_controlled_environment = {
    'OPENAI_API_KEY': 'offline-fixture-key',
    'KEV_BASE_URL': '',
    'OPENAI_BASE_URL': 'http://127.0.0.1:9/v1',
    'LLM_MODEL': 'controlled-test',
    'LLM_MODE': 'live',
    'MEMORY_EXTRACTION_MODEL': 'qwen3.8-27b',
    'MEMORY_DREAM_MODEL': 'qwen3.8-27b',
    'DATABASE_URL': 'sqlite:///:memory:',
    'MERCURY_CHECKPOINT_PATH': str(Path(_runtime.name) / 'checkpoints.sqlite3'),
    'HUMAN_OPERATOR_TOKEN': '',
    'SHOPPING_WRITES_PAUSED': 'false',
    'BUSINESS_DATA_MODE': 'demo',
    'NO_PROXY': '127.0.0.1,localhost,::1',
    'no_proxy': '127.0.0.1,localhost,::1',
}
# Settings accepts case-insensitive aliases. Remove inherited spellings first
# so a lowercase parent credential cannot shadow the uppercase override.
for name in tuple(os.environ):
    if name.upper() in _controlled_environment or name.lower() in ('http_proxy', 'https_proxy', 'all_proxy'):
        del os.environ[name]
os.environ.update(_controlled_environment)

# Importing config defines Settings but does not instantiate it. Disable dotenv
# before database/main/test modules can create and cache the first Settings.
from app.core.config import Settings, get_settings

Settings.model_config['env_file'] = None
get_settings.cache_clear()

# New role ingress always executes the production Kev parser/transport contract.
# Inherited business tests use a controlled current-role response, not live routing
# acceptance. Dedicated routing tests explicitly replace this transport's chooser.
# Both decisions execute the same production parser/transport. calls contains ALL
# actual requests; entry_calls/policy_calls are purpose-aware views for exact counts.
# No test-name switches, external network fallbacks, or business-service bypasses.
import json
from types import SimpleNamespace
import httpx
import pytest


@pytest.fixture(autouse=True)
def controlled_kev_transport(monkeypatch):
    from app.services import kev_provider
    control = {'calls': [], 'entry_calls': [], 'policy_calls': [],
               'choose': lambda state: 'no', 'choose_policy': lambda state: 'no'}
    def handle(request):
        assert request.url == httpx.URL('http://kev-controlled.invalid/v1/systemone')
        payload = json.loads(request.content)
        control['calls'].append(payload)
        purpose = next(iter(payload['questions']))
        control['policy_calls' if purpose == 'policy' else 'entry_calls'].append(payload)
        choice = control['choose_policy' if purpose == 'policy' else 'choose'](payload['state'])
        if isinstance(choice, httpx.HTTPError):
            raise choice
        if isinstance(choice, Exception):
            raise httpx.ConnectError(str(choice), request=request)
        return httpx.Response(200, json={'model':'kev-latest', 'answers':{purpose:{
            'type':'choice', 'choice':choice,
            'probabilities':{key:float(key == choice) for key in kev_provider.CRITERIA}}}})
    with httpx.Client(transport=httpx.MockTransport(handle)) as fixture_client:
        monkeypatch.setattr(kev_provider, 'client', lambda:fixture_client)
        monkeypatch.setattr(kev_provider, 'get_settings', lambda:SimpleNamespace(kev_base_url='http://kev-controlled.invalid'))
        yield control


@pytest.fixture(autouse=True)
def controlled_policy_source(tmp_path, monkeypatch):
    """Offline worker-boundary double; this is NOT BGE retrieval verification.

    Preserve real fixture/index provenance and production policy projection. Only
    expensive model recall is controlled; production has no lexical fallback.
    """
    import shutil
    import sqlite3
    from app.core.config import ROOT_DIR
    from app.knowledge.corpus import FIXTURE_NAMES, load_corpus
    from app.knowledge.hybrid import build_parameters
    from app.mercury import policy
    from app.services.knowledge_service import knowledge, check_budget

    root = tmp_path / 'controlled-policy'
    fixtures = root / 'data/fixtures'
    fixtures.mkdir(parents=True)
    for name in FIXTURE_NAMES:
        shutil.copyfile(ROOT_DIR / 'data/fixtures' / name, fixtures / name)
    index = root / 'data/indexes/hybrid.sqlite3'
    index.parent.mkdir()
    control = {'root': root, 'calls': []}

    def rebuild(version=None):
        corpus = json.loads((fixtures / 'policies.json').read_text())
        if version is not None:
            corpus['version'] = version
            (fixtures / 'policies.json').write_text(json.dumps(corpus, ensure_ascii=False))
        _documents, manifest = load_corpus(fixtures)
        manifest.update(build_parameters())
        with sqlite3.connect(index) as db:
            db.execute('CREATE TABLE IF NOT EXISTS manifest (content TEXT)')
            db.execute('DELETE FROM manifest')
            db.execute('INSERT INTO manifest VALUES (?)', (json.dumps(manifest),))
        control.update(corpus=corpus, manifest=manifest)

    def search(query, namespace, *, limit=10, allowed_ids=None, category=None,
               deadline=None, should_stop=None, expected_index_revision=None):
        if deadline is not None:
            check_budget(deadline, should_stop)
        assert namespace == 'policy', 'Controlled policy worker cannot simulate product or graph retrieval'
        control['calls'].append((query, category))
        keywords = {'refund': ('退款', '取消', '未发货', '仅退款'),
                    'return': ('退货', '七天', '7天', '签收', '生鲜', '不可退'),
                    'delivery': ('配送', '送达', '物流', '多久送到'),
                    'price': ('价格', '优惠'), 'stock': ('库存', '缺货'),
                    'order': ('订单修改', '购物车'), 'fulfillment': ('漏送', '错送', '破损'),
                    'quality': ('品质', '新鲜', '质量'), 'safety': ('食品安全',), 'human': ('人工',)}
        rows = [row for row in control['corpus']['policies']
                if (category is None or row['category'] == category)
                and any(word in query for word in keywords[row['category']])][:limit]
        return {'manifest': control['manifest'], 'hits': [{'id': row['policy_id'], 'document': {
            'id': row['policy_id'], 'namespace': 'policy', 'category': row['category'],
            'title': row['title'], 'text': row['content'], 'source': {
                'file': 'policies.json', 'record_id': row['policy_id'],
                'version': control['corpus']['version'], 'name': control['corpus']['source_name']}}} for row in rows]}

    rebuild()
    control['change_version'] = rebuild
    monkeypatch.setattr(policy, 'get_settings', lambda: SimpleNamespace(root_dir=root))
    monkeypatch.setattr(knowledge, 'search', search)
    return control


@pytest.fixture(autouse=True)
def controlled_product_source(controlled_policy_source, monkeypatch):
    """Independent controlled product recall, never eligibility or Offer logic.

    Static documents and pi_client's explicit synthetic Cola document simulate
    the external worker. Tests may supply a literal ranking. This does not test
    BGE quality or a real built index; policy stays in its own namespace double.
    """
    from app.knowledge.corpus import load_corpus
    from app.services.knowledge_service import knowledge, check_budget
    documents, _manifest = load_corpus(controlled_policy_source['root'] / 'data/fixtures')
    product_documents = {doc['id']:doc for doc in documents if doc['namespace'] == 'product'}
    product_documents['pi-cola'] = {'id':'pi-cola', 'namespace':'product', 'title':'测试可乐',
        'text':'Cola 测试可乐', 'source':{'file':'controlled-products', 'record_id':'pi-cola'}}
    policy_search = knowledge.search
    control = {'documents':product_documents, 'ranking':None, 'calls':[], 'extra_hits':[]}

    def search(query, namespace, *, limit=10, allowed_ids=None, category=None,
               deadline=None, should_stop=None, expected_index_revision=None):
        if namespace == 'policy':
            return policy_search(query, namespace, limit=limit, allowed_ids=allowed_ids,
                category=category, deadline=deadline, should_stop=should_stop,
                expected_index_revision=expected_index_revision)
        assert namespace == 'product', 'Controlled product worker cannot simulate graph or recipe retrieval'
        if deadline is not None:
            check_budget(deadline, should_stop)
        control['calls'].append({'query':query, 'allowed_ids':allowed_ids, 'limit':limit, 'deadline':deadline})
        if control.get('on_search'):
            control['on_search']()
        ids = control['ranking'] if control['ranking'] is not None else [identity for identity, doc in control['documents'].items()
            if query.lower() in (doc['title'] + ' ' + doc['text']).lower()]
        allowed = set(allowed_ids) if allowed_ids is not None else None
        ids = [identity for identity in ids if allowed is None or identity in allowed][:limit]
        hits = [{'id':identity, 'document':control['documents'][identity],
                 'ranks':{'sparse':rank}, 'scores':{'sparse':-1.0}, 'rrf_score':1/(60+rank)}
                for rank, identity in enumerate(ids, 1)]
        return {'manifest':controlled_policy_source['manifest'], 'hits':hits + control['extra_hits']}

    monkeypatch.setattr(knowledge, 'search', search)
    return control
