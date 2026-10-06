"""One role-aware source for both runtimes; no classifier or business authority."""
import json
from pathlib import Path

MODULES = json.loads(Path(__file__).with_name('experience.json').read_text())


def role_prompt(role):
    return MODULES['expression'][role] + ''.join(section['text'] for section in MODULES[role])


def keke_modules():
    return {'expression': MODULES['expression']['keke'], 'sections': MODULES['keke']}
