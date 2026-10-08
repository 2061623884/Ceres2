"""Fresh-index smoke on public fixture queries; prints IDs/ranks, not document text."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'backend'))
from app.knowledge.hybrid import search
from app.knowledge.bge import ROOT, MODEL_ID, MODEL_REVISION, DIMENSIONS

CASES = [
    ('recipe', '番茄炒蛋', 'dish-fanqie-chao-dan'),
    ('product', '炒饭用的虾仁', 'demo:shrimp-200g'),
    ('policy', '未发货取消订单', 'P-REF-01'),
    ('policy', '生鲜坏了能退吗', 'P-QUA-01'),
    ('policy', '火星定制商品特殊条款', None),
    ('policy', '怎么修自行车', None),
]

def main():
    rows=[]
    index=ROOT/'data/indexes/hybrid.sqlite3'
    for namespace, query, target in CASES:
        started=time.monotonic()
        result=search(index, query, namespace, fixtures=ROOT/'data/fixtures')
        rows.append({
            'namespace':namespace, 'query':query, 'expected_id':target,
            'sparse_top5':[{'id':identity,'rank':rank+1,'score':score} for rank,(identity,score) in enumerate(result['sparse'][:5])],
            'dense_top5':[{'id':identity,'rank':rank+1,'cosine':round(score,6)} for rank,(identity,score) in enumerate(result['dense'][:5])],
            'rrf_top5':[{'id':item['id'],'rrf_score':round(item['rrf_score'],8),'ranks':item['ranks']} for item in result['candidates'][:5]],
            'hits_top5':[{'id':item['id'],'rrf_score':round(item['rrf_score'],8)} for item in result['hits'][:5]],
            'expected_id_rank_sparse':next((i+1 for i,(identity,_) in enumerate(result['sparse']) if identity==target),None),
            'expected_id_rank_dense':next((i+1 for i,(identity,_) in enumerate(result['dense']) if identity==target),None),
            'expected_id_rank_rrf':next((i+1 for i,item in enumerate(result['candidates']) if item['id']==target),None),
            'expected_id_in_hits':any(item['id']==target for item in result['hits']),
            'duration_ms':round((time.monotonic()-started)*1000,1),
            'index_revision':result['manifest']['corpus_revision'],
        })
    print(json.dumps({'model':MODEL_ID,'revision':MODEL_REVISION,'dimensions':DIMENSIONS,'queries':rows},ensure_ascii=False))

if __name__=='__main__': main()
