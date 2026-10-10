# Public retrieval development metrics (v2) - macro and micro recall

This is a diagnostic summary of the 18-case public development set, not independent quality acceptance.

- Evaluation `optimization-retrieval-dev-v1` SHA-256: `eb47a57f89fc65d56d3e74a9b68947d096ba485d5c08051f29dc9a97aa12652e`.
- Raw report SHA-256: `8cc721432f7a48a8370d073a53edb490addc0eba8d1e16299063126206f19c22`.
- Index SHA-256: `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`; BGE revision `7999e1d3359715c523056ef9478215996d62a620`, 512 dimensions.
- Existing retrieval smoke: 18/18 cases passed. This is the calibrated development set.

This corrected v2 report adds query-macro Recall@5 to the prior gold-ID-weighted micro Recall@5. Ceres1-style macro recall is the unweighted mean of each answerable query's recall; a query with no target ID in top 5 scores zero. Micro recall weights each gold target ID equally. MRR@5 takes the first gold ID per answerable query, scores misses as zero, and keeps every answerable query in the denominator. BM25 and dense no-answer counts below describe raw candidate presence, not final false positives; the RRF column uses relevance-filtered final hits. The v1 report and raw output remain unchanged.

## Query counts and timing

| Namespace | Cases | Answerable | Gold IDs | No-answer | Timing unknown |
|---|---:|---:|---:|---:|---:|
| policy | 8 | 6 | 11 | 2 | 8 |
| product | 6 | 4 | 6 | 2 | 6 |
| recipe | 4 | 3 | 3 | 1 | 4 |

## Lane metrics

| Namespace | Lane | Macro Recall@5 | Micro Gold Recall@5 | Gold IDs @5 | MRR@5 | Answerable misses | No-answer candidates in top 5 | No-answer final RRF hits | Unique canonical IDs | Noncanonical IDs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| policy | bm25 | 1.0 | 1.0 | 11 | 1.0 | 0 | 2 | — | 11 | 0 |
| policy | dense | 1.0 | 1.0 | 11 | 0.916667 | 0 | 2 | — | 11 | 0 |
| policy | rrf | 1.0 | 1.0 | 11 | 0.916667 | 0 | 0 | 0 | 10 | 0 |
| product | bm25 | 0.75 | 0.833333 | 5 | 0.75 | 1 | 1 | — | 73 | 0 |
| product | dense | 1.0 | 1.0 | 6 | 1.0 | 0 | 2 | — | 73 | 0 |
| product | rrf | 1.0 | 1.0 | 6 | 1.0 | 0 | 0 | 0 | 18 | 0 |
| recipe | bm25 | 1.0 | 1.0 | 3 | 1.0 | 0 | 0 | — | 8 | 0 |
| recipe | dense | 1.0 | 1.0 | 3 | 1.0 | 0 | 1 | — | 8 | 0 |
| recipe | rrf | 1.0 | 1.0 | 3 | 1.0 | 0 | 0 | 0 | 6 | 0 |

All returned IDs in the captured lanes mapped to canonical IDs in the matching namespace of this verified index. The report has no search duration fields, so all 18 query timings remain unknown.
