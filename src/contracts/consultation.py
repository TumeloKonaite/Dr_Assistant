from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Likelihood = Literal["high", "moderate", "lower"]
SafetySeverity = Literal["warning", "blocker"]
RedFlagUrgency = Literal["urgent", "emergent"]
EvidenceLevel = Literal["sparse", "limited", "adequate"]
ConfidenceAlignment = Literal["aligned", "overstated"]
SafetyStatus = Literal["clear", "warning", "blocked"]


class ContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ConsultationCase(ContractModel):
    patient_id: str | None = None
    chief_complaint: str = Field(min_length=1)
    symptoms: list[str] = Field(default_factory=list)
    duration: str | None = None
    severity: str | None = None
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    history: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    transcript: str = Field(min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_id": "P-1024",
                "chief_complaint": "Chest pain",
                "symptoms": ["chest tightness", "shortness of breath", "nausea"],
                "duration": "2 hours",
                "severity": "severe",
                "medications": ["lisinopril"],
                "allergies": ["penicillin"],
                "history": ["hypertension"],
                "risk_factors": ["smoking", "family history of heart disease"],
                "transcript": "Patient reports sudden chest tightness and shortness of breath that started two hours ago.",
            }
        }
    )


class RetrievedCondition(ContractModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    matched_symptoms: list[str] = Field(default_factory=list)
    score: float = Field(ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "acute coronary syndrome",
                "description": "A spectrum of conditions caused by reduced blood flow to the heart.",
                "matched_symptoms": ["chest tightness", "shortness of breath", "nausea"],
                "score": 0.92,
            }
        }
    )


class DifferentialDiagnosis(ContractModel):
    condition_name: str = Field(min_length=1)
    likelihood: Likelihood
    reasoning: str = Field(min_length=1)
    supporting_findings: list[str] = Field(default_factory=list)
    conflicting_findings: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_tests: list[str] = Field(default_factory=list)
    urgency: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "condition_name": "acute coronary syndrome",
                "likelihood": "high",
                "reasoning": "Chest pain with shortness of breath and nausea makes acute coronary syndrome an important consideration, but the available information is still incomplete.",
                "supporting_findings": [
                    "sudden chest tightness",
                    "shortness of breath",
                    "nausea",
                ],
                "conflicting_findings": [
                    "No ECG, troponin, or exam findings are available yet.",
                ],
                "missing_information": ["ECG findings", "troponin result", "radiation of pain"],
                "recommended_tests": ["ECG", "troponin"],
                "urgency": "urgent evaluation should be considered because chest pain and dyspnea can reflect a time-sensitive cardiopulmonary condition",
            }
        }
    )


class CarePlan(ContractModel):
    suggested_tests: list[str] = Field(default_factory=list)
    suggested_referrals: list[str] = Field(default_factory=list)
    follow_up: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    patient_advice: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "suggested_tests": ["ECG", "troponin", "chest X-ray"],
                "suggested_referrals": ["Emergency department", "Cardiology"],
                "follow_up": [
                    "Arrange urgent same-day in-person assessment.",
                    "Reassess promptly after initial testing to narrow the differential.",
                ],
                "red_flags": ["worsening chest pain", "syncope", "new shortness of breath at rest"],
                "patient_advice": [
                    "Seek urgent medical review if symptoms intensify or new concerning symptoms develop.",
                ],
                "rationale": "The plan prioritizes rapid evaluation for serious cardiopulmonary causes while preserving diagnostic uncertainty.",
            }
        }
    )


class ClinicalReasoningOutput(ContractModel):
    differentials: list[DifferentialDiagnosis] = Field(default_factory=list)
    care_plan: CarePlan

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "differentials": [
                    DifferentialDiagnosis.model_config["json_schema_extra"]["example"],
                ],
                "care_plan": CarePlan.model_config["json_schema_extra"]["example"],
            }
        }
    )


class SoapNote(ContractModel):
    subjective: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    assessment: str = Field(min_length=1)
    plan: str = Field(min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subjective": "Patient reports severe chest pain for two hours with nausea and dyspnea.",
                "objective": "No vitals or exam findings available from transcript alone.",
                "assessment": "Symptoms are concerning for acute coronary syndrome.",
                "plan": "Advise immediate emergency evaluation, cardiac workup, and escalation if symptoms worsen.",
            }
        }
    )


class PatientSummary(ContractModel):
    what_was_discussed: str = Field(min_length=1)
    what_the_doctor_may_check_next: list[str] = Field(default_factory=list)
    what_you_should_do_next: list[str] = Field(default_factory=list)
    when_to_get_urgent_help: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "what_was_discussed": "You described sudden chest tightness, shortness of breath, and nausea that started about two hours ago.",
                "what_the_doctor_may_check_next": [
                    "An ECG and blood tests to look for heart strain or injury.",
                    "A chest X-ray if the doctor needs to check your lungs or other causes of chest pain.",
                ],
                "what_you_should_do_next": [
                    "Get urgent in-person medical assessment today.",
                    "Follow the clinician's instructions for immediate evaluation and testing.",
                ],
                "when_to_get_urgent_help": [
                    "Chest pain that gets worse or does not settle.",
                    "Fainting, severe trouble breathing, or new shortness of breath at rest.",
                ],
            }
        }
    )


class DocumentationBundle(ContractModel):
    soap_note: SoapNote
    patient_summary: PatientSummary

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "soap_note": SoapNote.model_config["json_schema_extra"]["example"],
                "patient_summary": PatientSummary.model_config["json_schema_extra"][
                    "example"
                ],
            }
        }
    )


class DetectedRedFlag(ContractModel):
    code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    urgency: RedFlagUrgency
    evidence: list[str] = Field(default_factory=list)
    patient_summary_terms: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "cardiopulmonary_emergency",
                "title": "Chest pain with dyspnea or syncope",
                "summary": "Chest pain plus shortness of breath or fainting can reflect a time-sensitive cardiopulmonary emergency.",
                "urgency": "emergent",
                "evidence": ["chest pain", "shortness of breath"],
                "patient_summary_terms": [
                    "chest pain",
                    "shortness of breath",
                    "fainting",
                ],
            }
        }
    )


class SafetyIssue(ContractModel):
    code: str = Field(min_length=1)
    severity: SafetySeverity
    source: str = Field(min_length=1)
    message: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "definitive_diagnosis_claim",
                "severity": "blocker",
                "source": "patient_summary",
                "message": "Generated output states a definitive diagnosis that is not supported by the structured evidence.",
                "evidence": ["The patient has pneumonia."],
            }
        }
    )


class UncertaintyAssessment(ContractModel):
    evidence_level: EvidenceLevel
    confidence_alignment: ConfidenceAlignment
    explicit_uncertainty_present: bool
    missing_information_documented: bool
    supported_high_likelihood_differentials: bool
    summary: str = Field(min_length=1)
    issues: list[SafetyIssue] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "evidence_level": "limited",
                "confidence_alignment": "aligned",
                "explicit_uncertainty_present": True,
                "missing_information_documented": True,
                "supported_high_likelihood_differentials": True,
                "summary": "The case has limited evidence, but the reasoning keeps uncertainty explicit and documents missing data.",
                "issues": [],
            }
        }
    )


class SafetyReport(ContractModel):
    status: SafetyStatus
    red_flags: list[DetectedRedFlag] = Field(default_factory=list)
    red_flag_summary: str = Field(min_length=1)
    issues: list[SafetyIssue] = Field(default_factory=list)
    uncertainty_assessment: UncertaintyAssessment
    warning_count: int = Field(ge=0)
    blocker_count: int = Field(ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "warning",
                "red_flags": [
                    DetectedRedFlag.model_config["json_schema_extra"]["example"],
                ],
                "red_flag_summary": "Urgent red flags detected: Chest pain with dyspnea or syncope.",
                "issues": [
                    SafetyIssue.model_config["json_schema_extra"]["example"],
                ],
                "uncertainty_assessment": UncertaintyAssessment.model_config[
                    "json_schema_extra"
                ]["example"],
                "warning_count": 0,
                "blocker_count": 1,
            }
        }
    )


class FinalConsultationBundle(ContractModel):
    case: ConsultationCase
    differentials: list[DifferentialDiagnosis] = Field(default_factory=list)
    care_plan: CarePlan
    soap_note: SoapNote
    patient_summary: PatientSummary
    safety: SafetyReport | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "case": ConsultationCase.model_config["json_schema_extra"]["example"],
                "differentials": [
                    DifferentialDiagnosis.model_config["json_schema_extra"]["example"],
                    {
                        "condition_name": "pulmonary embolism",
                        "likelihood": "moderate",
                        "reasoning": "Chest pain and shortness of breath also keep pulmonary embolism on the differential, although the history is incomplete.",
                        "supporting_findings": [
                            "chest pain",
                            "shortness of breath",
                        ],
                        "conflicting_findings": [
                            "No oxygen saturation, leg symptoms, or thromboembolic risk history are available.",
                        ],
                        "missing_information": ["oxygen saturation", "leg swelling", "recent immobility"],
                        "recommended_tests": ["pulse oximetry", "D-dimer if clinically appropriate"],
                        "urgency": "urgent assessment should be considered if symptoms are worsening or associated with hypoxia",
                    },
                ],
                "care_plan": CarePlan.model_config["json_schema_extra"]["example"],
                "soap_note": SoapNote.model_config["json_schema_extra"]["example"],
                "patient_summary": PatientSummary.model_config["json_schema_extra"][
                    "example"
                ],
                "safety": SafetyReport.model_config["json_schema_extra"]["example"],
            }
        }
    )
