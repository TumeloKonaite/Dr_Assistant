from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Likelihood = Literal["high", "medium", "low"]


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
    condition: str = Field(min_length=1)
    likelihood: Likelihood
    reasoning: str = Field(min_length=1)
    missing_information: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "condition": "acute coronary syndrome",
                "likelihood": "high",
                "reasoning": "Chest pain with shortness of breath and nausea raises concern for cardiac ischemia.",
                "missing_information": ["ECG findings", "troponin result", "radiation of pain"],
            }
        }
    )


class CarePlan(ContractModel):
    suggested_tests: list[str] = Field(default_factory=list)
    referrals: list[str] = Field(default_factory=list)
    follow_up: str = Field(min_length=1)
    red_flags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "suggested_tests": ["ECG", "troponin", "chest X-ray"],
                "referrals": ["Emergency department", "Cardiology"],
                "follow_up": "Immediate emergency evaluation is recommended today.",
                "red_flags": ["worsening chest pain", "syncope", "new shortness of breath at rest"],
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


class FinalConsultationBundle(ContractModel):
    case: ConsultationCase
    differentials: list[DifferentialDiagnosis] = Field(default_factory=list)
    care_plan: CarePlan
    soap_note: SoapNote
    patient_summary: str = Field(min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "case": ConsultationCase.model_config["json_schema_extra"]["example"],
                "differentials": [
                    DifferentialDiagnosis.model_config["json_schema_extra"]["example"],
                    {
                        "condition": "pulmonary embolism",
                        "likelihood": "medium",
                        "reasoning": "Chest pain and shortness of breath also warrant evaluation for thromboembolic disease.",
                        "missing_information": ["oxygen saturation", "leg swelling", "recent immobility"],
                    },
                ],
                "care_plan": CarePlan.model_config["json_schema_extra"]["example"],
                "soap_note": SoapNote.model_config["json_schema_extra"]["example"],
                "patient_summary": "Your symptoms could represent a serious heart or lung problem, so you should get urgent in-person evaluation today.",
            }
        }
    )
