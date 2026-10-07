"""Graph build identity, verified before a query can contact its model provider."""
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from urllib.parse import urlsplit

from app.core.config import get_settings
from app.knowledge.bge import MODEL_ID, MODEL_REVISION, DIMENSIONS
from app.knowledge.corpus import FIXTURE_NAMES, CORPUS_REVISION, manifest_revision

GRAPH_REVISION = 'ceres-recipe-byog-v4'
PROVIDER_REVISION = 'ceres-graphrag-provider-v2'


class GraphIndexMissingError(FileNotFoundError):
    pass


class GraphStaleError(ValueError):
    pass


def source_identity(fixtures):
    settings = get_settings()
    folder = Path(__file__).parent
    return {'graph_revision': GRAPH_REVISION, 'corpus_revision': CORPUS_REVISION,
            'graphrag': version('graphrag'),
            'embedding_model': MODEL_ID, 'embedding_revision': MODEL_REVISION,
            'dimensions': DIMENSIONS, 'completion_model': settings.llm_model,
            'provider_host': urlsplit(settings.openai_base_url).hostname,
            'provider_revision': PROVIDER_REVISION,
            'files': {name: hashlib.sha256((fixtures / name).read_bytes()).hexdigest() for name in FIXTURE_NAMES},
            'graph_implementation': {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                for name in ('graph.py', 'providers.py', 'graph_context.py', 'graph_manifest.py', 'corpus.py', 'bge.py')}}


def artifact_identity(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for directory in ('output', 'prompts') for path in sorted((root / directory).rglob('*')) if path.is_file()}


def validate_graph(root, fixtures, expected_revision=None):
    path = root / 'manifest.json'
    if not path.is_file():
        raise GraphIndexMissingError('Graph index has not been built')
    manifest = json.loads(path.read_text())
    if expected_revision is not None and manifest_revision(manifest) != expected_revision:
        raise GraphStaleError('Graph build changed during this query')
    expected = source_identity(fixtures)
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise GraphStaleError('Graph fixture, model or implementation changed')
    artifacts = artifact_identity(root)
    required = {f'output/{name}.parquet' for name in ('entities', 'relationships', 'text_units', 'communities', 'community_reports')}
    if not required.issubset(artifacts) or not any(name.startswith('output/lancedb/') for name in artifacts):
        raise GraphIndexMissingError('Graph tables or embeddings are missing')
    if artifacts != manifest.get('artifacts'):
        raise GraphStaleError('Graph artifacts changed after build')
    return manifest
