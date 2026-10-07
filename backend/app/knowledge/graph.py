"""Deterministic BYOG inputs plus real Microsoft GraphRAG indexing and queries."""
import json
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlparse
from pydantic import BaseModel, ConfigDict, StrictInt
from app.core.config import get_settings
from app.knowledge.bge import DIMENSIONS, MODEL_ID, MODEL_REVISION
from app.knowledge.corpus import load_corpus

GRAPH_REVISION = 'ceres-recipe-byog-v3'
QUERY_REVISION = 'canonical-scope-overview-v3'
SELECTION_FORMAT = '''只输出一个 JSON 对象，严格为 {"entity_numbers":[0,1]}，数组必须为整数，不要输出任何其他字段、文本、用量、分类或未知判断。数字必须取自实体表id列或原始事实的 [Data: Entities (数字)]；不要使用报告、关系、来源的数字，不要用中文名称或自行拼实体ID。根据用户问题选择有关实体，明确询问用某食材的菜时只选原始描述有此必需食材的菜；询问食材种类时也选择相关INGREDIENT实体。没有原始事实支持的问题返回空数组。最终名称、分类和用量将由宿主从原始实体事实呈现。'''
WORKFLOWS = ['create_communities', 'create_community_reports', 'generate_text_embeddings']


class EvidenceSelection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    entity_numbers: list[StrictInt]
REPORT_RULES = '''Ceres 菜谱采购资料约束：社区只是全图的局部子图。菜谱 RECIPE 的 description 中是完整必需食材清单，报告必须逐项保留名称、基准人数和已有用量，即使某食材节点或关系位于社区外。不能从社区内缺少某个关系推断全图没有记录它。将完整食材清单写入一个明确 finding，并以该 RECIPE 的 entity id 引用。SKU 的 category_id 是货架位置，不能当作食材类别、成分或营养类别；食材种类只能引用 INGREDIENT 的 kind。图路径不能证明替代、过敏安全、营养或家庭已有数量。不要重复泛化风险套话，准确保留原始采购事实。\n\n'''
QUERY_RULES = '''Ceres 约束：报告仅覆盖各自社区子图，不是单个菜谱的完整全图关系清单。每份报告附有规范原始实体事实，此节优先于生成摘要，直接依据它核对食材种类、菜名和用量。摘要漏项不能用来断言原始菜谱、采购候选或全图未记录该食材；资料不充分时保持未知，不猜测或作否定断言。食材类别仅用 INGREDIENT 的 kind；SKU 货架 category_id 不作食材或营养分类。\n\n'''


def export_graph(fixtures: Path, root: Path) -> dict:
    import pandas as pd
    import tiktoken
    documents, manifest = load_corpus(fixtures)
    dishes = json.loads((fixtures / 'recipes.json').read_text())['dishes']
    ingredients = json.loads((fixtures / 'ingredients.json').read_text())['ingredients']
    used = {row['ingredient_id'] for dish in dishes for row in dish['required_items']} | {i for dish in dishes for i in dish['pantry_items']}
    products = [p for p in json.loads((fixtures / 'products.json').read_text())['products'] if p['review_status'] == 'approved' and used.intersection(p['ingredient_ids'])]
    doc_ids = {d['dish_id'] for d in dishes} | {p['sku_id'] for p in products}
    selected = [d for d in documents if d['id'] in doc_ids]
    nodes, edges = {}, []
    def node(identity, title, kind, description):
        nodes[identity] = {'id': identity, 'title': f'{title} [{identity}]', 'type': kind,
            'description': description, 'text_unit_ids': []}
    for dish in dishes:
        node('recipe:'+dish['dish_id'], dish['name'], 'RECIPE', next(d['text'] for d in selected if d['id'] == dish['dish_id']))
    for ingredient in ingredients:
        node('ingredient:'+ingredient['ingredient_id'], ingredient['name_zh'], 'INGREDIENT',
            f"采购食材 {ingredient['name_zh']}，类别 {ingredient['kind']}；来源 ingredients.json/{ingredient['ingredient_id']}。采购关系不证明配料、营养、过敏安全或跨食材替代。")
    for product in products:
        node('sku:'+product['sku_id'], product['name_zh'] or product['name'], 'SKU', next(d['text'] for d in selected if d['id'] == product['sku_id']) + '。仅供模拟采购，价格库存另查当前业务 Offer。')
    def edge(source, target, description, text_id):
        identity = f'{source}->{target}'
        edges.append({'id': identity, 'source': nodes[source]['title'], 'target': nodes[target]['title'],
            'description': description, 'weight': 1.0, 'text_unit_ids': [text_id]})
        for identity in (source, target):
            nodes[identity]['text_unit_ids'].append(text_id)
    for dish in dishes:
        for item in dish['required_items']:
            quantity = ' '.join(f"{item['quantity_'+u]:g}{u}" for u in ('g', 'ml', 'pc') if 'quantity_'+u in item)
            edge('recipe:'+dish['dish_id'], 'ingredient:'+item['ingredient_id'],
                f"REQUIRES: {dish['name']} 基准 {dish['base_people']} 人需 {quantity}，原始用量来源 recipes.json/{dish['dish_id']}；其他人数和包装由业务服务计算。", 'text:'+dish['dish_id'])
        for ingredient in dish['pantry_items']:
            edge('recipe:'+dish['dish_id'], 'ingredient:'+ingredient,
                f"PANTRY: {dish['name']} 调料，数量未记录，不能推定家庭已有或足够。", 'text:'+dish['dish_id'])
    for product in products:
        for ingredient in used.intersection(product['ingredient_ids']):
            edge('ingredient:'+ingredient, 'sku:'+product['sku_id'],
                f"PROCUREMENT_CANDIDATE: {product['name_zh']} 可作为该食材采购候选，销售规格 {product['spec_quantity']:g}{product['spec_unit']}；仍须核对单位、门店库存及用户约束，不证明食品成分或替代。", 'text:'+product['sku_id'])
    degrees = Counter(endpoint for e in edges for endpoint in (e['source'], e['target']))
    entities = []
    for index, node_row in enumerate(nodes.values()):
        entities.append({**node_row, 'human_readable_id': index,
            'text_unit_ids': sorted(set(node_row['text_unit_ids'])), 'frequency': len(set(node_row['text_unit_ids'])),
            'degree': degrees[node_row['title']]})
    relationships = [{**e, 'human_readable_id': i,
        'combined_degree': degrees[e['source']]+degrees[e['target']]} for i, e in enumerate(edges)]
    tokenizer = tiktoken.get_encoding('cl100k_base')
    text_units = []
    for index, document in enumerate(selected):
        text_id = 'text:'+document['id']
        text_units.append({'id': text_id, 'human_readable_id': index, 'text': document['title']+' '+document['text'],
            'n_tokens': len(tokenizer.encode(document['text'])), 'document_id': document['id'],
            'entity_ids': [e['id'] for e in entities if text_id in e['text_unit_ids']],
            'relationship_ids': [e['id'] for e in relationships if text_id in e['text_unit_ids']], 'covariate_ids': []})
    output = root / 'output'
    output.mkdir(parents=True, exist_ok=True)
    from graphrag.prompts.index.community_report import COMMUNITY_REPORT_PROMPT
    from graphrag.prompts.query.global_search_reduce_system_prompt import REDUCE_SYSTEM_PROMPT
    from graphrag.prompts.query.global_search_map_system_prompt import MAP_SYSTEM_PROMPT
    prompts = root/'prompts'
    prompts.mkdir(parents=True, exist_ok=True)
    (prompts/'community_report.txt').write_text(REPORT_RULES+COMMUNITY_REPORT_PROMPT)
    (prompts/'global_reduce.txt').write_text(QUERY_RULES+REDUCE_SYSTEM_PROMPT)
    (prompts/'global_map.txt').write_text(QUERY_RULES+MAP_SYSTEM_PROMPT)
    for name, records in (('entities', entities), ('relationships', relationships), ('text_units', text_units), ('documents', selected)):
        pd.DataFrame(records).to_parquet(output / (name+'.parquet'), index=False)
    manifest.update({'graph_revision': GRAPH_REVISION, 'graphrag': version('graphrag'), 'workflows': WORKFLOWS,
        'embedding_model': MODEL_ID, 'embedding_revision': MODEL_REVISION, 'dimensions': DIMENSIONS,
        'graph_counts': {'entities': len(entities), 'relationships': len(relationships), 'text_units': len(text_units)}})
    return manifest


def config(root: Path):
    from graphrag.config.models.graph_rag_config import GraphRagConfig
    from app.knowledge.providers import register
    register()
    settings = get_settings()
    return GraphRagConfig(
        completion_models={'chat': {'type': 'ceres_json_mode', 'model_provider': 'openai',
            'model': settings.llm_model, 'api_base': settings.openai_base_url,
            'api_key': settings.openai_api_key, 'metrics': None}},
        embedding_models={'bge': {'type': 'ceres_bge', 'model_provider': 'local', 'model': MODEL_ID, 'metrics': None}},
        concurrent_requests=2,
        input_storage={'type': 'file', 'base_dir': str(root/'input')},
        output_storage={'type': 'file', 'base_dir': str(root/'output')},
        update_output_storage={'type': 'file', 'base_dir': str(root/'update')},
        reporting={'type': 'file', 'base_dir': str(root/'logs')},
        cache={'type': 'memory'},
        vector_store={'type': 'lancedb', 'db_uri': str(root/'output/lancedb'), 'vector_size': DIMENSIONS},
        workflows=WORKFLOWS, cluster_graph={'use_lcc': False},
        embed_text={'embedding_model_id': 'bge', 'names': ['text_unit_text', 'entity_description', 'community_full_content']},
        community_reports={'completion_model_id': 'chat', 'graph_prompt': str(root/'prompts/community_report.txt')},
        local_search={'completion_model_id': 'chat', 'embedding_model_id': 'bge'},
        global_search={'completion_model_id': 'chat', 'map_prompt': str(root/'prompts/global_map.txt'), 'reduce_prompt': str(root/'prompts/global_reduce.txt')})


def ground_reports(root: Path):
    """Preserve selected communities' original node facts beside LLM summaries.

    Global search uses community reports, which can lose cross-community recipe
    edges. These explicit witnesses preserve the complete source descriptions;
    generated summaries are retained, and embedding runs on the augmented text.
    """
    import pandas as pd
    output = root/'output'
    entities = pd.read_parquet(output/'entities.parquet').set_index('id')
    communities = pd.read_parquet(output/'communities.parquet').set_index('community')
    reports = pd.read_parquet(output/'community_reports.parquet')
    for index, report in reports.iterrows():
        members = communities.loc[report['community'], 'entity_ids']
        facts = []
        for identity in sorted(members):
            entity = entities.loc[identity]
            facts.append(f"[Data: Entities ({entity['human_readable_id']})] {entity['type']} {entity['title']}：{entity['description']}")
        reports.at[index, 'full_content'] += '\n\n## 规范原始实体事实（优先于生成摘要）\n'+'\n'.join(facts)
    reports.to_parquet(output/'community_reports.parquet', index=False)


async def build(fixtures: Path, root: Path) -> dict:
    from graphrag import api
    from app.knowledge.providers import CALLS, PROVIDER_REVISION
    CALLS.clear()
    (root/'manifest.json').unlink(missing_ok=True)
    manifest = export_graph(fixtures, root)
    pipeline = config(root)
    # Keep real official workflows. Ground the reports before the official
    # community embeddings are generated, so text and vector inputs agree.
    results = await api.build_index(config=pipeline.model_copy(update={'workflows': WORKFLOWS[:2]}))
    for result in results:
        if result.error is not None:
            raise result.error
    ground_reports(root)
    embeddings = await api.build_index(config=pipeline.model_copy(update={'workflows': WORKFLOWS[2:]}))
    for result in embeddings:
        if result.error is not None:
            raise result.error
    import pandas as pd
    manifest['output_counts'] = {name: len(pd.read_parquet(root/'output'/f'{name}.parquet')) for name in ('entities', 'relationships', 'text_units', 'communities', 'community_reports')}
    manifest['completion_model'] = get_settings().llm_model
    manifest['provider_host'] = urlparse(get_settings().openai_base_url).hostname
    manifest['provider_revision'] = PROVIDER_REVISION
    manifest['community_grounding'] = 'canonical-entity-witness-v1'
    manifest['calls'] = list(CALLS)
    (root/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    return manifest


async def search(root: Path, query: str, method: str) -> dict:
    import pandas as pd
    from graphrag import api
    from app.knowledge.providers import CALLS
    from graphrag.prompts.query.global_search_reduce_system_prompt import NO_DATA_ANSWER
    offset = len(CALLS)
    output = root/'output'
    tables = {name: pd.read_parquet(output/f'{name}.parquet') for name in ('entities', 'relationships', 'text_units', 'communities', 'community_reports')}
    query_config = config(root)
    query_config.completion_models['chat'].call_args = {'response_format': {'type':'json_object'}}
    common = {'config': query_config, 'entities': tables['entities'], 'communities': tables['communities'],
        'community_reports': tables['community_reports'], 'community_level': int(tables['communities']['level'].max()),
        'response_type': SELECTION_FORMAT, 'query': query}
    if method == 'local':
        answer, context = await api.local_search(**common, text_units=tables['text_units'], relationships=tables['relationships'], covariates=None)
    else:
        answer, context = await api.global_search(**common, dynamic_community_selection=False)
    projected_context = {key: json.loads(value.to_json(orient='records', force_ascii=False)) if isinstance(value, pd.DataFrame) else value for key, value in context.items()}
    titles = {row['entity'] for row in projected_context.get('entities', [])}
    for relation in projected_context.get('relationships', []):
        titles.update((relation['source'], relation['target']))
    scope = set(tables['entities'].loc[tables['entities']['title'].isin(titles), 'id'])
    report_ids = {str(row['id']) for row in projected_context.get('reports', [])}
    for _, report in tables['community_reports'].iterrows():
        if str(report['human_readable_id']) in report_ids:
            community = tables['communities'].loc[tables['communities']['community'] == report['community']].iloc[0]
            scope.update(community['entity_ids'])
    selected = EvidenceSelection(entity_numbers=[]) if answer == NO_DATA_ANSWER else EvidenceSelection.model_validate_json(answer)
    allowed_numbers = {int(row['human_readable_id']) for _, row in tables['entities'].iterrows() if row['id'] in scope}
    if set(selected.entity_numbers) - allowed_numbers:
        raise ValueError('GraphRAG selected a reference outside the retrieved context')
    records = tables['entities'].set_index('human_readable_id')
    # Invalid references fail instead of becoming generated merchant facts.
    # Global is an overview of retrieved communities. Keep the complete source
    # view, instead of asking another LLM selection to discard graph facts.
    # Empty unsupported queries stay empty. Local keeps the focused selection.
    fact_numbers = sorted(allowed_numbers) if method == 'global' and selected.entity_numbers else list(dict.fromkeys(selected.entity_numbers))
    facts = [{'id':records.loc[number,'id'], 'type':records.loc[number,'type'], 'title':records.loc[number,'title'],
        'description':records.loc[number,'description'], 'human_readable_id':number}
        for number in fact_numbers]
    titles_to_id = dict(zip(tables['entities']['title'], tables['entities']['id']))
    facts_by_id = {fact['id']:fact for fact in facts}
    ingredient_recipes = {}
    for _, relationship in tables['relationships'].iterrows():
        if not relationship['description'].startswith('REQUIRES:'):
            continue
        recipe_id, ingredient_id = titles_to_id[relationship['source']], titles_to_id[relationship['target']]
        if recipe_id in facts_by_id and ingredient_id in facts_by_id:
            entry = ingredient_recipes.setdefault(ingredient_id, {'ingredient':facts_by_id[ingredient_id]['title'], 'recipes':[]})
            entry['recipes'].append({'recipe_id':recipe_id, 'title':facts_by_id[recipe_id]['title'],
                'relationship_id':relationship['id'], 'source_description':relationship['description']})
    rendered = '\n'.join(f"{fact['description']} [Data: Entities ({fact['human_readable_id']})]" for fact in facts) if facts else '当前规范知识中没有取得可核对的相关事实；未知事项需另行确认。'
    if method == 'global' and facts:
        rendered = '以下是本次检索社区的规范事实视图，基准用量不表示实际采购件数：\n'+rendered
        rendered += '\n\n按必需食材关联的菜谱：\n'+'\n'.join(f"{entry['ingredient']}："+'、'.join(row['title'] for row in entry['recipes']) for entry in ingredient_recipes.values())
    return {'query': query, 'method': method, 'answer': rendered, 'selection': selected.model_dump(),
        'canonical_facts': facts, 'ingredient_recipes':ingredient_recipes, 'query_revision': QUERY_REVISION,
        'context': projected_context,
        'source_map': {'entities': tables['entities'][['id', 'human_readable_id', 'title']].to_dict('records'),
            'relationships': tables['relationships'][['id', 'human_readable_id', 'source', 'target']].to_dict('records')},
        'manifest': json.loads((root/'manifest.json').read_text()), 'calls': CALLS[offset:]}
