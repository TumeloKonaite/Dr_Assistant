from src.contracts.consultation import ConsultationCase, DifferentialDiagnosis
from src.tools.uncertainty_calibration_tool import assess_uncertainty


def make_sparse_case() -> ConsultationCase:
    return ConsultationCase(
        chief_complaint="Fatigue",
        symptoms=["fatigue"],
        transcript="Patient reports fatigue.",
    )


def make_richer_case() -> ConsultationCase:
    return ConsultationCase(
        chief_complaint="Chest pain",
        symptoms=["chest pain", "shortness of breath", "nausea"],
        duration="2 hours",
        severity="severe",
        history=["hypertension"],
        risk_factors=["smoking"],
        transcript="Patient reports chest pain, shortness of breath, and nausea for two hours.",
    )


def test_assess_uncertainty_warns_when_sparse_evidence_is_overconfident():
    assessment = assess_uncertainty(
        make_sparse_case(),
        [
            DifferentialDiagnosis(
                condition_name="anemia",
                likelihood="moderate",
                reasoning="Anemia explains the fatigue.",
                supporting_findings=["fatigue"],
                conflicting_findings=[],
                missing_information=["CBC"],
                recommended_tests=["CBC"],
                urgency=None,
            )
        ],
    )

    assert assessment.confidence_alignment == "overstated"
    assert any(issue.code == "sparse_case_overconfidence" for issue in assessment.issues)


def test_assess_uncertainty_passes_when_uncertainty_and_missing_information_are_explicit():
    assessment = assess_uncertainty(
        make_richer_case(),
        [
            DifferentialDiagnosis(
                condition_name="acute coronary syndrome",
                likelihood="high",
                reasoning="Chest pain and dyspnea make acute coronary syndrome possible, but the current information is incomplete.",
                supporting_findings=["chest pain", "shortness of breath"],
                conflicting_findings=["No ECG or troponin results are available."],
                missing_information=["ECG", "troponin", "exam findings"],
                recommended_tests=["ECG", "troponin"],
                urgency="Urgent assessment should be considered.",
            )
        ],
    )

    assert assessment.issues == []
    assert assessment.explicit_uncertainty_present is True
    assert assessment.missing_information_documented is True
    assert assessment.supported_high_likelihood_differentials is True


def test_assess_uncertainty_verifies_stronger_differentials_include_support_and_missing_information():
    assessment = assess_uncertainty(
        make_richer_case(),
        [
            DifferentialDiagnosis(
                condition_name="pulmonary embolism",
                likelihood="high",
                reasoning="Pulmonary embolism is likely.",
                supporting_findings=["shortness of breath"],
                conflicting_findings=[],
                missing_information=[],
                recommended_tests=["D-dimer"],
                urgency="Urgent assessment should be considered.",
            )
        ],
    )

    codes = {issue.code for issue in assessment.issues}

    assert "high_likelihood_without_support" in codes
    assert "missing_information_not_documented" in codes
    assert assessment.supported_high_likelihood_differentials is False
