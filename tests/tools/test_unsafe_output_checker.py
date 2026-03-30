from src.contracts.consultation import (
    CarePlan,
    ConsultationCase,
    DetectedRedFlag,
    DifferentialDiagnosis,
    PatientSummary,
    SoapNote,
)
from src.tools.unsafe_output_checker import check_generated_outputs


def make_case() -> ConsultationCase:
    return ConsultationCase(
        chief_complaint="Cough",
        symptoms=["cough", "fever"],
        transcript="Patient reports cough and fever for three days.",
    )


def make_differentials(reasoning: str = "Pneumonia is possible, but the exam and imaging are not available yet.") -> list[DifferentialDiagnosis]:
    return [
        DifferentialDiagnosis(
            condition_name="pneumonia",
            likelihood="moderate",
            reasoning=reasoning,
            supporting_findings=["cough", "fever"],
            conflicting_findings=["No exam findings are available."],
            missing_information=["oxygen saturation", "lung exam"],
            recommended_tests=["chest X-ray"],
            urgency=None,
        )
    ]


def make_care_plan(
    follow_up: list[str] | None = None,
    patient_advice: list[str] | None = None,
) -> CarePlan:
    return CarePlan(
        suggested_tests=["chest X-ray"],
        suggested_referrals=["Primary care"],
        follow_up=follow_up or ["Follow up after the recommended evaluation."],
        red_flags=["worsening shortness of breath"],
        patient_advice=patient_advice or ["Seek urgent help if breathing worsens."],
        rationale="The plan focuses on reassessment because the current evidence is incomplete.",
    )


def make_soap_note(
    objective: str = "No vital signs, examination findings, laboratory results, or imaging results were available in the source materials.",
    assessment: str = "Pneumonia remains one possible explanation pending more evaluation.",
    plan: str = "Arrange further assessment and testing if symptoms persist or worsen.",
) -> SoapNote:
    return SoapNote(
        subjective="Patient reports cough and fever for three days.",
        objective=objective,
        assessment=assessment,
        plan=plan,
    )


def make_patient_summary(
    what_was_discussed: str = "You described cough and fever for the last three days.",
    what_you_should_do_next: list[str] | None = None,
    when_to_get_urgent_help: list[str] | None = None,
) -> PatientSummary:
    return PatientSummary(
        what_was_discussed=what_was_discussed,
        what_the_doctor_may_check_next=["A chest X-ray or exam if symptoms continue."],
        what_you_should_do_next=what_you_should_do_next or ["Follow up if the cough worsens."],
        when_to_get_urgent_help=when_to_get_urgent_help or ["Get urgent help for worsening breathing difficulty."],
    )


def test_check_generated_outputs_blocks_definitive_diagnosis_wording():
    issues = check_generated_outputs(
        case=make_case(),
        differentials=make_differentials(),
        care_plan=make_care_plan(),
        soap_note=make_soap_note(assessment="The patient has pneumonia."),
        patient_summary=make_patient_summary(),
    )

    assert any(issue.code == "definitive_diagnosis_claim" for issue in issues)
    assert any(issue.severity == "blocker" for issue in issues)


def test_check_generated_outputs_blocks_invented_objective_findings():
    issues = check_generated_outputs(
        case=make_case(),
        differentials=make_differentials(),
        care_plan=make_care_plan(),
        soap_note=make_soap_note(objective="Vitals show fever of 39.2 C and oxygen saturation of 88 percent."),
        patient_summary=make_patient_summary(),
    )

    assert any(issue.code == "invented_objective_data" for issue in issues)


def test_check_generated_outputs_blocks_medication_or_dosing_instructions():
    issues = check_generated_outputs(
        case=make_case(),
        differentials=make_differentials(),
        care_plan=make_care_plan(patient_advice=["Start amoxicillin 500 mg three times daily."]),
        soap_note=make_soap_note(),
        patient_summary=make_patient_summary(),
    )

    assert any(issue.code == "medication_or_dosing_instruction" for issue in issues)


def test_check_generated_outputs_blocks_unsupported_treatment_or_disposition_commands():
    issues = check_generated_outputs(
        case=make_case(),
        differentials=make_differentials(),
        care_plan=make_care_plan(follow_up=["Discharge home with no further workup."]),
        soap_note=make_soap_note(),
        patient_summary=make_patient_summary(),
    )

    assert any(issue.code == "unsupported_treatment_or_disposition" for issue in issues)


def test_check_generated_outputs_warns_when_upstream_red_flags_are_missing_from_patient_summary():
    red_flags = [
        DetectedRedFlag(
            code="cardiopulmonary_emergency",
            title="Chest pain with dyspnea or syncope",
            summary="Chest pain plus shortness of breath or fainting can reflect a time-sensitive cardiopulmonary emergency.",
            urgency="emergent",
            evidence=["chest pain", "shortness of breath"],
            patient_summary_terms=["chest pain", "shortness of breath", "fainting"],
        )
    ]

    issues = check_generated_outputs(
        case=make_case(),
        differentials=make_differentials(),
        care_plan=make_care_plan(),
        soap_note=make_soap_note(),
        patient_summary=make_patient_summary(
            what_was_discussed="You described chest discomfort earlier.",
            what_you_should_do_next=["Follow up soon."],
            when_to_get_urgent_help=["Get help if you feel worse."],
        ),
        detected_red_flags=red_flags,
    )

    assert any(issue.code == "red_flag_omission_in_patient_summary" for issue in issues)
    assert any(issue.severity == "warning" for issue in issues)
