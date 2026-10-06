"""Typed preference interpretation at the existing Pi semantic boundary."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class HistoryDefaults(BaseModel):
    model_config = ConfigDict(extra='forbid')
    people: int | None = Field(default=None, gt=0, strict=True)
    budget_fen: int | None = Field(default=None, ge=0, strict=True)
    exclusions: list[str] | None = None


class HistoryMemoryRef(BaseModel):
    model_config = ConfigDict(extra='forbid')
    memory_id: str
    revision: int = Field(ge=1, strict=True)


class HistoryCommand(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['list', 'select']
    source_task_id: str | None = None
    memory_defaults: HistoryDefaults = Field(default_factory=HistoryDefaults)
    memory_refs: list[HistoryMemoryRef] = Field(default_factory=list)
