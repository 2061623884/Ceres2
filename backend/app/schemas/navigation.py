"""Public role choices and host-generated navigation actions, never write grants."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Role = Literal['keke', 'momo']


class SelectedObject(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['product', 'order']
    id: str = Field(min_length=1, max_length=100)


class EntryJudgment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    outcome: Literal['yes', 'no', 'uncertain', 'timeout', 'error', 'not_attempted']
    elapsed_ms: float | None
    reason: str | None


class RouteDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    routing_request_id: str
    opening_id: str
    original_message: str
    selected_object: SelectedObject | None
    source_role: Role
    target_role: Role
    authorized_role: Role | None
    status: Literal['ready', 'switch']
    show_prompt: bool
    continue_original: Literal[False]
    capability: None
    criteria_version: str
    anchor: tuple[int, str | None, int]
    entry_judgment: EntryJudgment | None = None
    legacy_replay: bool = False
    provider_output: dict | None = None
    provider_error: str | None = None
    message: str | None = None


class SwitchRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    opening_id: str
    target_role: Role
    accept: bool
    routing_request_id: str | None = None


class RoleSwitchAction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: Literal['switch_role'] = 'switch_role'
    session_id: str
    request: SwitchRequest
