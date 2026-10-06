"""Single joint decision using Ceres ee7ce104's public Kev SystemOne contract.

Only the choice criteria change: no second call and no Mercury capability enum.
Live compatibility of these criteria is a separate acceptance gate.
"""
from functools import lru_cache
from typing import Literal
import httpx
from pydantic import BaseModel, Field, field_validator
from app.core.config import get_settings

CRITERIA_VERSION = 'ceres2-role-capability-v2-explicit-return'
Choice = Literal['keke_exploration', 'keke_purchase_modification', 'keke_factual_qa', 'keke_chat', 'momo', 'clarify', 'return_keke', 'return_keke_exploration', 'return_keke_purchase_modification', 'return_keke_factual_qa', 'return_keke_chat']
CRITERIA = {
    'keke_exploration': 'Shopping/product or dish exploration. Preserve complex multiple goals for Keke; do not extract parameters.',
    'keke_purchase_modification': 'Modify an existing purchase goal/list. Missing details stay with Keke, never grant write permission.',
    'keke_factual_qa': 'Shopping facts or general store policy when current_role is keke. General policy needs no order.',
    'keke_chat': 'Greetings or ordinary conversation when current_role is keke. No purchase goal is implied.',
    'momo': 'Specific placed orders/after-sales, or general policies/greetings when current_role is momo. No shopping capability label applies.',
    'clarify': 'Service ownership itself is unresolved, even using recent dialogue. Missing business parameters alone are not a reason.',
    'return_keke': 'The user explicitly asks only to return to shopping/Keke from Momo, with no remaining business or conversation request. Navigation only, no transaction permission.',
    'return_keke_exploration': 'The user explicitly chooses to return to Keke NOW and also requests shopping/product/dish exploration. Preserve the entire compound request for Keke; do not ask for the same page-switch consent again.',
    'return_keke_purchase_modification': 'The user explicitly chooses to return to Keke NOW and also requests changing a purchase goal/list. Page navigation is already chosen; preserve the original text and all confirmation boundaries.',
    'return_keke_factual_qa': 'The user explicitly chooses to return to Keke NOW and also requests facts or general store policy. Navigate and let Keke answer the whole original request.',
    'return_keke_chat': 'The user explicitly chooses to return to Keke NOW and also continues ordinary conversation without a purchase goal. No purchase task is implied.',
}
INSTRUCTIONS = '''Classify SERVICE ownership and, only for Keke-owned requests, one bounded capability in ONE choice.
Keke handles shopping, products and purchase lists; Momo handles specific placed orders and after-sales.
Both answer GENERAL policies and greetings in the current role, even without a selected order.
The latest explicit request overrides old topics. A considered product is not a placed order.
Do not choose tools, order steps, extract business parameters, judge parameter completeness, or authorize writes.
Do not drop any part of complex/multiple-goal text; the main model receives the full original text.
A new shopping goal without an explicit page choice uses keke_* and still needs the user to choose a role switch.
An explicit return NOW with a remaining request uses return_keke_* in the SAME joint choice; the suffix is only the usual Keke capability.
Pure page-only return uses return_keke. Conditional future navigation or quoted return words are not an explicit current page choice.
For compound return plus shopping, preserve every clause, constraint and question for the main model; page choice never authorizes adding to cart.'''


class ChoiceAnswer(BaseModel):
    type: Literal['choice']
    choice: Choice
    probabilities: dict[Choice, float] = Field(min_length=len(CRITERIA), max_length=len(CRITERIA))

    @field_validator('probabilities')
    @classmethod
    def probabilities_in_range(cls, values):
        if any(not 0 <= value <= 1 for value in values.values()):
            raise ValueError('Kev probabilities must be between zero and one')
        return values


class Answers(BaseModel):
    service: ChoiceAnswer


class KevResponse(BaseModel):
    model: Literal['kev-latest']
    answers: Answers


class KevUnavailable(Exception):
    pass


@lru_cache(maxsize=1)
def client():
    return httpx.Client(timeout=3.0)


def judge(state):
    endpoint = get_settings().kev_base_url
    if not endpoint:
        raise KevUnavailable('Kev endpoint is not configured')
    payload = {'state': state, 'model': 'kev-latest', 'questions': {'service': {
        'type': 'choice', 'instructions': INSTRUCTIONS, 'criteria': CRITERIA}}}
    try:
        response = client().post(endpoint.rstrip('/') + '/v1/systemone', json=payload)
        response.raise_for_status()
        raw = response.json()
        return KevResponse.model_validate(raw).answers.service.choice, raw
    except (httpx.HTTPError, ValueError) as exc:
        raise KevUnavailable(f'{type(exc).__name__}: {exc}') from exc
