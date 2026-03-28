from __future__ import annotations

from agents import Agent, function_tool

from src.contracts.consultation import ConsultationCase
from src.tools.illness_retrieval_tool import retrieve_conditions


@function_tool
def retrieve_conditions_tool(case: dict, top_k: int = 5) -> list[dict]:
    """
    Retrieve relevant illness candidates for a structured consultation case.
    Retrieval only: no diagnosis, treatment, or next-step planning.
    """
    parsed_case = ConsultationCase.model_validate(case)
    results = retrieve_conditions(parsed_case, top_k=top_k)
    return [result.model_dump() for result in results]


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
