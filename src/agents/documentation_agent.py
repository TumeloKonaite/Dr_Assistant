from __future__ import annotations

from src.agents._compat import Agent, function_tool
from src.contracts.consultation import (
    CarePlan,
    ConsultationCase,
    DifferentialDiagnosis,
    DocumentationBundle,
)
from src.tools.patient_summary_tool import generate_patient_summary
from src.tools.soap_note_tool import generate_soap


def run_documentation(
    case: ConsultationCase,
    differentials: list[DifferentialDiagnosis],
    plan: CarePlan,
    safety_context: str | None = None,
) -> DocumentationBundle:
    soap_note = generate_soap(
        case=case,
        differentials=differentials,
        plan=plan,
        safety_context=safety_context,
    )
    patient_summary = generate_patient_summary(
        case=case,
        plan=plan,
        safety_context=safety_context,
    )
    return DocumentationBundle(
        soap_note=soap_note,
        patient_summary=patient_summary,
    )


@function_tool
def documentation_tool(
    case: ConsultationCase,
    differentials: list[DifferentialDiagnosis],
    plan: CarePlan,
    safety_context: str | None = None,
) -> DocumentationBundle:
    """
    Generate clinician- and patient-facing documentation from structured
    clinical reasoning outputs.
    """
    return run_documentation(
        case,
        differentials,
        plan,
        safety_context=safety_context,
    )


documentation_agent = Agent(
    name="documentation_agent",
    instructions=(
        "You coordinate documentation generation after structured clinical "
        "reasoning. Generate a SOAP note and a patient-facing summary from "
        "trusted structured inputs only. "
        "Do not add prompt logic of your own and do not introduce definitive "
        "diagnoses, invented findings, or treatment decisions."
    ),
    tools=[documentation_tool],
    model="gpt-5-nano",
)
