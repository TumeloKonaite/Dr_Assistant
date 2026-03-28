from __future__ import annotations

from src.agents._compat import Agent, function_tool

from src.contracts.consultation import ConsultationCase, RetrievedCondition
from src.tools.illness_retrieval_tool import retrieve_conditions


@function_tool
def retrieve_conditions_tool(
    case: ConsultationCase,
    top_k: int = 5,
) -> list[RetrievedCondition]:
    """
    Retrieve relevant illness candidates for a structured consultation case.
    Retrieval only: no diagnosis, treatment, or next-step planning.
    """
    return retrieve_conditions(case, top_k=top_k)


retrieval_agent = Agent(
    name="retrieval_agent",
    instructions=(
        "You retrieve relevant illness candidates from the illness knowledge base "
        "using a structured consultation case. "
        "You only perform retrieval and ranking. "
        "Do not diagnose, recommend treatment, or produce downstream clinical reasoning."
    ),
    tools=[retrieve_conditions_tool],
    model="gpt-5-nano",
)
