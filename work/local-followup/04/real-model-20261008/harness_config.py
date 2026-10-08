"""Shared dotenv source and environment fields for this local evaluation harness."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values


SOURCE_ENV = Path('/data/amax/Documents/projects/Agent/Agent产品/Ceres2/.env')
FIELDS = {
    'main_provider': ('OPENAI_BASE_URL', 'OPENAI_API_KEY', 'LLM_MODEL', 'LLM_MODE'),
    'memory_extraction': ('MEMORY_EXTRACTION_MODEL',),
    'memory_dream': ('MEMORY_DREAM_MODEL',),
    'kev': ('KEV_BASE_URL',),
}
MEMORY_DREAM_REQUIRED_FIELDS = (
    *FIELDS['main_provider'], *FIELDS['memory_extraction'], *FIELDS['memory_dream'],
)

# These are all application Settings environment aliases. Remove inherited
# values before installing the explicitly selected harness configuration.
APP_SETTINGS_ENV_FIELDS = (
    'DATABASE_URL', 'LLM_MODE', 'KEV_BASE_URL', 'SHOPPING_WRITES_PAUSED',
    'HUMAN_OPERATOR_TOKEN', 'BUSINESS_DATA_MODE', 'OPENAI_BASE_URL',
    'OPENAI_API_KEY', 'LLM_MODEL', 'MEMORY_EXTRACTION_MODEL',
    'MEMORY_DREAM_MODEL', 'MERCURY_CHECKPOINT_PATH',
)


def read_source_values(source: Path | str = SOURCE_ENV) -> dict[str, str | None]:
    source_path = Path(source)
    return dotenv_values(source_path, interpolate=False) if source_path.is_file() else {}


def is_nonempty(values: dict[str, str | None], field: str) -> bool:
    value = values.get(field)
    return value is not None and bool(str(value).strip())


def missing_fields(values: dict[str, str | None], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if not is_nonempty(values, field)]


def apply_harness_environment(selected: dict[str, str]) -> None:
    application_fields = {field.casefold() for field in APP_SETTINGS_ENV_FIELDS}
    for field in tuple(os.environ):
        if field.casefold() in application_fields:
            os.environ.pop(field)
    os.environ.update(selected)
