from __future__ import annotations

from src.agents._compat import Agent, function_tool

from src.contracts.consultation import (
    ClinicalReasoningOutput,
    ConsultationCase,
    RetrievedCondition,
)
from src.tools.care_plan_tool import generate_care_plan
from src.tools.differential_generation_tool import generate_differentials


def run_planner(
    case: ConsultationCase,
    retrieved: list[RetrievedCondition],
    safety_context: str | None = None,
) -> ClinicalReasoningOutput:
    differentials = generate_differentials(
        case=case,
        retrieved=retrieved,
        safety_context=safety_context,
    )
    care_plan = generate_care_plan(
        case=case,
        differentials=differentials,
        safety_context=safety_context,
    )
    return ClinicalReasoningOutput(
        differentials=differentials,
        care_plan=care_plan,
    )


@function_tool
def planner_tool(
    case: ConsultationCase,
    retrieved: list[RetrievedCondition],
    safety_context: str | None = None,
) -> ClinicalReasoningOutput:
    """
    Generate structured differential reasoning and a care plan for a
    consultation case.
    """
    return run_planner(case, retrieved, safety_context=safety_context)


planner_agent = Agent(
    name="planner_agent",
    instructions=(
        "You coordinate structured clinical reasoning after retrieval. "
        "Generate differentials first, then generate a care plan from those "
        "differentials. "
        "Do not add prompt logic of your own and do not produce definitive "
        "diagnoses or treatment decisions."
    ),
    tools=[planner_tool],
    model="gpt-5-nano",
)
