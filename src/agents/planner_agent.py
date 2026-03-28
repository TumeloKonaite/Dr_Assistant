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
) -> ClinicalReasoningOutput:
    differentials = generate_differentials(case=case, retrieved=retrieved)
    care_plan = generate_care_plan(case=case, differentials=differentials)
    return ClinicalReasoningOutput(
        differentials=differentials,
        care_plan=care_plan,
    )


@function_tool
def planner_tool(
    case: ConsultationCase,
    retrieved: list[RetrievedCondition],
) -> ClinicalReasoningOutput:
    """
    Generate structured differential reasoning and a care plan for a
    consultation case.
    """
    return run_planner(case, retrieved)


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
