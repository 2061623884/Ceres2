"""Configuration shared by the Python authority and both model runtimes."""
from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / '.env', extra='ignore', populate_by_name=True)
    database_url: str = Field('sqlite:///data/runtime/ceres2.sqlite3', alias='DATABASE_URL')
    llm_mode: str = Field('live', alias='LLM_MODE')
    kev_base_url: str = Field('', alias='KEV_BASE_URL')
    # Scoped operational hold: only cart/checkout mutation routes use it.
    shopping_writes_paused: bool = Field(False, alias='SHOPPING_WRITES_PAUSED')
    human_operator_token: str = Field('', alias='HUMAN_OPERATOR_TOKEN')
    business_data_mode: Literal['demo'] = Field('demo', alias='BUSINESS_DATA_MODE')
    openai_base_url: str = Field('', alias='OPENAI_BASE_URL')
    openai_api_key: str = Field('', alias='OPENAI_API_KEY')
    llm_model: str = Field('', alias='LLM_MODEL')
    memory_extraction_model: str = Field('qwen3.8-27b', alias='MEMORY_EXTRACTION_MODEL')
    memory_dream_model: str = Field('qwen3.8-27b', alias='MEMORY_DREAM_MODEL')
    mercury_checkpoint_path: Path = Field(ROOT_DIR / 'data/runtime/mercury-checkpoints.sqlite3', alias='MERCURY_CHECKPOINT_PATH')

    @field_validator('mercury_checkpoint_path')
    @classmethod
    def resolve_checkpoint_path(cls, path: Path) -> Path:
        return path if path.is_absolute() else ROOT_DIR / path

    @property
    def root_dir(self) -> Path:
        return ROOT_DIR

    def is_live_llm_configured(self) -> bool:
        return self.llm_mode == 'live' and bool(self.openai_base_url and self.openai_api_key and self.llm_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
