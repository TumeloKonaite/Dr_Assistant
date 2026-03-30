from __future__ import annotations

from src.contracts.consultation import (
    ConsultationCase,
    DifferentialDiagnosis,
    SafetyIssue,
    UncertaintyAssessment,
)


UNCERTAINTY_MARKERS = (
    "possible",
    "possibly",
    "may",
    "might",
    "could",
    "consider",
    "uncertain",
    "incomplete",
    "limited",
    "pending",
    "not yet",
    "one possible",
)


def _is_sparse_case(case: ConsultationCase) -> bool:
    structured_signal_count = sum(
        1
        for value in (
            len(case.symptoms),
            len(case.history),
            len(case.risk_factors),
            len(case.medications),
            1 if case.duration else 0,
            1 if case.severity else 0,
        )
        if value
    )
    return structured_signal_count <= 2


def assess_uncertainty(
    case: ConsultationCase,
    differentials: list[DifferentialDiagnosis],
) -> UncertaintyAssessment:
    issues: list[SafetyIssue] = []
    sparse_case = _is_sparse_case(case)
    explicit_uncertainty_present = True
    missing_information_documented = True
    supported_high_likelihood_differentials = True

    for item in differentials:
        reasoning_lower = item.reasoning.lower()
        reasoning_has_uncertainty = any(marker in reasoning_lower for marker in UNCERTAINTY_MARKERS)
        if not reasoning_has_uncertainty:
            explicit_uncertainty_present = False

        if not item.missing_information:
            missing_information_documented = False
            issues.append(
                SafetyIssue(
                    code="missing_information_not_documented",
                    severity="warning",
                    source="uncertainty_calibration",
                    message=f"Differential '{item.condition_name}' does not document missing information.",
                    evidence=[item.condition_name],
                )
            )

        if item.likelihood == "high":
            has_support = len(item.supporting_findings) >= 2
            supported_high_likelihood_differentials = (
                supported_high_likelihood_differentials and has_support
            )
            if not has_support:
                issues.append(
                    SafetyIssue(
                        code="high_likelihood_without_support",
                        severity="warning",
                        source="uncertainty_calibration",
                        message=f"High-likelihood differential '{item.condition_name}' has insufficient supporting evidence.",
                        evidence=[item.condition_name],
                    )
                )

    if sparse_case and not explicit_uncertainty_present:
        issues.append(
            SafetyIssue(
                code="sparse_case_overconfidence",
                severity="warning",
                source="uncertainty_calibration",
                message="Sparse-input case does not keep uncertainty explicit in the generated reasoning.",
                evidence=[case.chief_complaint],
            )
        )

    if sparse_case:
        evidence_level = "sparse"
    elif len(case.symptoms) <= 2:
        evidence_level = "limited"
    else:
        evidence_level = "adequate"

    confidence_alignment = (
        "aligned"
        if not any(issue.code in {"sparse_case_overconfidence", "high_likelihood_without_support"} for issue in issues)
        else "overstated"
    )

    if issues:
        summary = (
            "The generated reasoning needs clearer calibration between confidence and available evidence."
        )
    elif evidence_level == "sparse":
        summary = "The case is sparse, but uncertainty is explicit and unsupported certainty was avoided."
    else:
        summary = "Confidence is proportional to the currently available evidence and missing information is documented."

    return UncertaintyAssessment(
        evidence_level=evidence_level,
        confidence_alignment=confidence_alignment,
        explicit_uncertainty_present=explicit_uncertainty_present,
        missing_information_documented=missing_information_documented,
        supported_high_likelihood_differentials=supported_high_likelihood_differentials,
        summary=summary,
        issues=issues,
    )
