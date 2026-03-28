from unittest.mock import patch

from src.agents.documentation_agent import run_documentation
from src.contracts.consultation import (
    CarePlan,
    ConsultationCase,
    DifferentialDiagnosis,
    DocumentationBundle,
    PatientSummary,
    SoapNote,
)


def make_case() -> ConsultationCase:
    return ConsultationCase(
        patient_id="P-7001",
        chief_complaint="Fatigue",
        symptoms=["fatigue"],
        duration="1 week",
        transcript="Patient reports fatigue for one week.",
    )


def make_differentials() -> list[DifferentialDiagnosis]:
    return [
        DifferentialDiagnosis(
            condition_name="anemia",
            likelihood="moderate",
            reasoning="Fatigue makes anemia plausible, but the presentation is nonspecific and testing is not available yet.",
            supporting_findings=["fatigue"],
            conflicting_findings=["No CBC or exam findings are available."],
            missing_information=["CBC", "bleeding history"],
            recommended_tests=["CBC"],
            urgency=None,
        )
    ]


def make_care_plan() -> CarePlan:
    return CarePlan(
        suggested_tests=["CBC"],
        suggested_referrals=["Primary care"],
        follow_up=["Review history, examination, and initial laboratory results before narrowing the differential."],
        red_flags=["fainting", "chest pain"],
        patient_advice=["Seek urgent review if you develop chest pain or fainting."],
        rationale="The plan emphasizes basic testing and reassessment because the current presentation is sparse.",
    )


def make_soap_note() -> SoapNote:
    return SoapNote(
        subjective="Patient reports fatigue for one week.",
        objective="No vital signs, examination findings, laboratory results, or imaging results were available in the source materials.",
        assessment="Fatigue is nonspecific and requires further evaluation; anemia remains one possible explanation.",
        plan="Arrange basic testing and reassessment after results are available.",
    )


def make_patient_summary() -> PatientSummary:
    return PatientSummary(
        what_was_discussed="You reported fatigue that has lasted about a week.",
        what_the_doctor_may_check_next=["A blood test to look for common causes of fatigue."],
        what_you_should_do_next=["Follow up after the recommended tests."],
        when_to_get_urgent_help=["Get urgent help if you faint or develop chest pain."],
    )


def test_run_documentation_composes_soap_and_patient_summary():
    case = make_case()
    differentials = make_differentials()
    care_plan = make_care_plan()
    soap_note = make_soap_note()
    patient_summary = make_patient_summary()

    with patch(
        "src.agents.documentation_agent.generate_soap",
        return_value=soap_note,
    ) as mock_generate_soap, patch(
        "src.agents.documentation_agent.generate_patient_summary",
        return_value=patient_summary,
    ) as mock_generate_patient_summary:
        result = run_documentation(case, differentials, care_plan)

    assert isinstance(result, DocumentationBundle)
    assert result.soap_note == soap_note
    assert result.patient_summary == patient_summary
    mock_generate_soap.assert_called_once_with(
        case=case,
        differentials=differentials,
        plan=care_plan,
    )
    mock_generate_patient_summary.assert_called_once_with(case=case, plan=care_plan)
