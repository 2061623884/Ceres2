"""Coco-only role entry using the existing Kev SystemOne transport contract."""
from functools import lru_cache
from typing import Literal
import httpx
from pydantic import BaseModel, Field, field_validator
from app.core.config import get_settings

CRITERIA_VERSION = 'ceres2-coco-role-entry-v1'
Choice = Literal['yes', 'no', 'uncertain']
CRITERIA = {
    'yes': 'The current request needs Momo to handle a specific placed order or after-sales case.',
    'no': 'The current request can stay with Coco, including shopping, general store policy and conversation.',
    'uncertain': 'Whether this request needs Momo cannot be determined from the current message and relevant context.',
}
INSTRUCTIONS = '''Does this new Coco message need Momo?
Momo handles specific placed orders and after-sales cases. Coco handles shopping, products, purchase lists, general policies and conversation.
General refund or return policy does not require an order or a role switch. A considered product is not a placed order.
Use the complete latest message and relevant recent dialogue. Missing shopping parameters alone do not require Momo.
Answer only yes, no or uncertain. Do not classify Coco capabilities, choose tools, extract business parameters, authorize business writes or change pages.
A yes only offers a switch; the user must choose it. Preserve every clause for the role that handles the original request.'''


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
    def __init__(self, reason, *, outcome='error'):
        super().__init__(reason)
        self.reason = reason
        self.outcome = outcome


@lru_cache(maxsize=1)
def client():
    return httpx.Client(timeout=3.0)


def judge(state):
    endpoint = get_settings().kev_base_url
    if not endpoint:
        raise KevUnavailable('not_configured')
    payload = {'state': state, 'model': 'kev-latest', 'questions': {'service': {
        'type': 'choice', 'instructions': INSTRUCTIONS, 'criteria': CRITERIA}}}
    try:
        response = client().post(endpoint.rstrip('/') + '/v1/systemone', json=payload)
        response.raise_for_status()
        raw = response.json()
        return KevResponse.model_validate(raw).answers.service.choice, raw
    except httpx.TimeoutException as exc:
        raise KevUnavailable(type(exc).__name__, outcome='timeout') from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise KevUnavailable(type(exc).__name__) from exc
