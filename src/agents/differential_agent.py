from __future__ import annotations

from src.agents._compat import Agent, function_tool

from src.contracts.consultation import (
    ConsultationCase,
    DifferentialDiagnosis,
    RetrievedCondition,
)
from src.tools.differential_generation_tool import generate_differentials


@function_tool
def differential_generation_tool(
    case: ConsultationCase,
    retrieved: list[RetrievedCondition],
) -> list[DifferentialDiagnosis]:
    """
    Generate a structured differential diagnosis list from a consultation case
    and retrieved candidate conditions.
    """
    return generate_differentials(case, retrieved)


differential_agent = Agent(
    name="differential_agent",
    instructions=(
        "You generate structured differential diagnoses from a consultation case "
        "and retrieved candidate conditions. "
        "You must remain cautious, avoid definitive diagnosis language, and "
        "return only schema-compliant differential outputs."
    ),
    tools=[differential_generation_tool],
    model="gpt-5-nano",
)
