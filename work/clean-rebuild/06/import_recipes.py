"""Select the exact approved static recipes; no archived application imports."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
source = root.parent / 'staging/static-catalog/chinese-dishes-v1.json'
destination = root / 'data/fixtures/recipes.json'
selection = ['dish-fanqie-chao-dan', 'dish-dan-chao-fan']
payload = json.loads(source.read_text())
dishes = {dish['dish_id']:dish for dish in payload['dishes']}
destination.write_text(json.dumps({'version':payload['version'], 'dishes':[dishes[key] for key in selection]}, ensure_ascii=False, indent=2) + '\n')
(root / 'work/clean-rebuild/06/recipe-provenance.json').write_text(json.dumps({
    'source':'../staging/static-catalog/chinese-dishes-v1.json',
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'selection':selection, 'destination':'data/fixtures/recipes.json',
    'destination_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
    'method':'Exact dish objects by ID; existing catalog already supplies rice/scallion. No archived runtime or state.'
},ensure_ascii=False,indent=2) + '\n')
