"""Real LangGraph confirmation interrupt; SQL receipts survive checkpoint loss."""
from contextlib import contextmanager
from typing import TypedDict
from uuid import uuid4
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from app.core.config import get_settings
from app.core.errors import AppError


class ApplicationState(TypedDict, total=False):
    request: dict
    proposal: dict
    proposal_id: str
    approval: dict
    receipt: dict
    recovery: bool
    intent_version: int


def build_application_graph(saver, service, owner_id, case_id, run_context=None):
    def accept_intent(state):
        return {'intent_version':service.accept_replacement(owner_id, case_id, state['request'], run_context)}

    def eligibility(state):
        try:
            service.eligibility(owner_id, case_id, state['request'], state['intent_version'], run_context)
        except AppError as error:
            detail = error.detail['error']
            raise AppError(error.status_code, detail['code'],
                detail['message'] + '；旧的待确认提案已失效，新的申请未提交。') from error
        return {}

    def proposal(state):
        preview = service.propose(owner_id, case_id, state['request'], state['proposal_id'], state['intent_version'], run_context)
        return {'proposal':preview, 'proposal_id':preview['proposal_id']}

    def await_confirmation(state):
        approval = interrupt({'type':'aftersales_confirmation', 'proposal_id':state['proposal_id']})
        return {'approval':approval}

    def apply(state):
        approval = state['approval']
        # The only producer of this resume payload is the confirmed:true HTTP
        # endpoint. Models cannot reach this node or supply approval content.
        return {'receipt':service.submit(owner_id, case_id, state['proposal_id'], approval['idempotency_key'])}

    builder = StateGraph(ApplicationState)
    builder.add_node('accept_intent', accept_intent)
    builder.add_node('eligibility', eligibility)
    builder.add_node('proposal', proposal)
    builder.add_node('await_confirmation', await_confirmation)
    builder.add_node('apply', apply)
    builder.add_node('receipt', lambda state: {'receipt':state['receipt']})
    builder.add_conditional_edges(START, lambda state: 'await_confirmation' if state.get('recovery') else 'accept_intent')
    builder.add_edge('accept_intent', 'eligibility')
    builder.add_edge('eligibility', 'proposal')
    builder.add_edge('proposal', 'await_confirmation')
    builder.add_edge('await_confirmation', 'apply')
    builder.add_edge('apply', 'receipt')
    builder.add_edge('receipt', END)
    return builder.compile(checkpointer=saver)


@contextmanager
def application_graph(service, owner_id, case_id, run_context=None):
    path = get_settings().mercury_checkpoint_path
    path.parent.mkdir(parents=True,exist_ok=True)
    with SqliteSaver.from_conn_string(str(path)) as saver:
        yield build_application_graph(saver, service, owner_id, case_id, run_context)


def propose(service, owner_id, case_id, request, run_context=None):
    # Proposal creation is not an application write. Its graph stops at the
    # interrupt and canonical read exposes the immutable preview after refresh.
    try:
        with application_graph(service,owner_id,case_id,run_context) as graph:
            proposal_id = f'asp-{uuid4().hex}'
            state=graph.invoke({'request':request,'proposal_id':proposal_id,'recovery':False},
                {'configurable':{'thread_id':f'aftersales:{case_id}:{proposal_id}'}})
            return state['proposal']
    except Exception as error:
        if run_context is None:
            service.record_failure(owner_id, case_id, error, selection_version=request['selection_version'])
        raise


def confirm(service, owner_id, case_id, proposal_id, key):
    receipt=service.replay(owner_id,case_id,proposal_id,key)
    if receipt is not None:
        return receipt
    # Resume the actual persistent proposal interrupt. If its checkpoint was
    # lost, reconstruct the wait from the immutable reference, never approval.
    try:
        with application_graph(service,owner_id,case_id) as graph:
            config={'configurable':{'thread_id':f'aftersales:{case_id}:{proposal_id}'}}
            snapshot = graph.get_state(config)
            if snapshot.next != ('await_confirmation',):
                graph.invoke({'proposal_id':proposal_id,'recovery':True},config)
            state=graph.invoke(Command(resume={'idempotency_key':key}),config)
            return state['receipt']
    except Exception as error:
        service.record_failure(owner_id, case_id, error, proposal_id=proposal_id)
        raise
