from unittest.mock import patch

from src.agents.planner_agent import run_planner
from src.contracts.consultation import (
    CarePlan,
    ClinicalReasoningOutput,
    ConsultationCase,
    DifferentialDiagnosis,
    RetrievedCondition,
)


def make_case() -> ConsultationCase:
    return ConsultationCase(
        patient_id="P-5001",
        chief_complaint="Fatigue",
        symptoms=["fatigue"],
        duration="1 week",
        transcript="Patient reports fatigue for one week.",
    )


def make_retrieved() -> list[RetrievedCondition]:
    return [
        RetrievedCondition(
            name="anemia",
            description="Reduced hemoglobin concentration.",
            matched_symptoms=["fatigue"],
            score=0.61,
        )
    ]


def make_differentials() -> list[DifferentialDiagnosis]:
    return [
        DifferentialDiagnosis(
            condition_name="anemia",
            likelihood="moderate",
            reasoning="Fatigue makes anemia plausible, but the presentation is nonspecific and key labs are not available.",
            supporting_findings=["fatigue"],
            conflicting_findings=["No CBC or exam findings are available."],
            missing_information=["CBC", "bleeding history", "dietary history"],
            recommended_tests=["CBC"],
            urgency=None,
        )
    ]


def make_care_plan() -> CarePlan:
    return CarePlan(
        suggested_tests=["CBC", "basic metabolic panel"],
        suggested_referrals=["Primary care"],
        follow_up=["Review history, exam, and initial laboratory results before narrowing the differential."],
        red_flags=["syncope", "progressive shortness of breath", "chest pain"],
        patient_advice=["Seek urgent review if new chest pain, fainting, or worsening breathlessness occurs."],
        rationale="The plan emphasizes further history, examination, and basic testing because the current presentation is sparse.",
    )


def test_run_planner_composes_differentials_and_care_plan():
    case = make_case()
    retrieved = make_retrieved()
    differentials = make_differentials()
    care_plan = make_care_plan()
    safety_context = "Urgent red flags detected: Severe shortness of breath."

    with patch(
        "src.agents.planner_agent.generate_differentials",
        return_value=differentials,
    ) as mock_generate_differentials, patch(
        "src.agents.planner_agent.generate_care_plan",
        return_value=care_plan,
    ) as mock_generate_care_plan:
        result = run_planner(case, retrieved, safety_context=safety_context)

    assert isinstance(result, ClinicalReasoningOutput)
    assert result.differentials == differentials
    assert result.care_plan == care_plan
    mock_generate_differentials.assert_called_once_with(
        case=case,
        retrieved=retrieved,
        safety_context=safety_context,
    )
    mock_generate_care_plan.assert_called_once_with(
        case=case,
        differentials=differentials,
        safety_context=safety_context,
    )
