# Browser fixture support Spec review

Frozen canonical commit: 5e172ef1983f858fd25bd153f24c7af213e59c19. Source support repository HEAD: ce90cc8c19e2e0c616a6a738759e17bb97eba239. Exact cmp comparisons of all six source files against the separate frozen support repository found no differences. This commit adds only six support files and SOURCE.json under work/local-cloud-integration/browser-support. Reviewed inclusion diff and sources; no execution.

No actionable Spec finding in the inclusion delta. This is bounded Tester support, not a production browser endpoint: fresh synthetic DB/checkpoint/owner, scripted loopback models, controlled retrieval, explicitly disabled memory worker, .env refusal before imports, source hashes, cleanup and required Node guard configuration. The fixture bootstrap is confined to its unique generated host; cookie is host-only and CSP restricts external resources. No product module or configured model changed by this inclusion.

README and SOURCE.json explicitly distinguish controlled HTTP/DOM from browser, real BGE/GraphRAG relevance, live-provider, and user acceptance. Relocation execution is marked pending and cannot be inferred from byte equivalence. Chromium EPERM/official CUA loopback refusal do not become browser passes. The complete branch remains unaccepted until its applicable gates are established or explicitly reported blocked/not run.
