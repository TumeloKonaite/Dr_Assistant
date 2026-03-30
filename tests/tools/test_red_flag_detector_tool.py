from src.contracts.consultation import ConsultationCase
from src.tools.red_flag_detector_tool import detect_red_flags, summarize_red_flags


def make_case(transcript: str, symptoms: list[str], severity: str | None = None) -> ConsultationCase:
    return ConsultationCase(
        chief_complaint=symptoms[0] if symptoms else "Concern",
        symptoms=symptoms,
        severity=severity,
        transcript=transcript,
    )


def test_detect_red_flags_flags_chest_pain_with_dyspnea():
    case = make_case(
        transcript="Patient reports chest pain and shortness of breath that started suddenly.",
        symptoms=["chest pain", "shortness of breath"],
        severity="severe",
    )

    red_flags = detect_red_flags(case)

    assert any(flag.code == "cardiopulmonary_emergency" for flag in red_flags)
    assert "Chest pain with dyspnea or syncope" in summarize_red_flags(red_flags)


def test_detect_red_flags_flags_severe_headache_with_neurologic_symptoms():
    case = make_case(
        transcript="Patient says this is the worst headache of her life with new weakness and confusion.",
        symptoms=["headache", "weakness"],
    )

    red_flags = detect_red_flags(case)

    assert any(flag.code == "neurologic_headache_red_flag" for flag in red_flags)


def test_detect_red_flags_flags_gi_bleeding_terms():
    case = make_case(
        transcript="Patient reports black stools and vomiting blood overnight.",
        symptoms=["abdominal pain", "black stools"],
    )

    red_flags = detect_red_flags(case)

    assert any(flag.code == "gi_bleeding" for flag in red_flags)


def test_detect_red_flags_flags_suicidal_or_self_harm_language():
    case = make_case(
        transcript="Patient says they want to die and have thought about killing themselves.",
        symptoms=["depressed mood"],
    )

    red_flags = detect_red_flags(case)

    assert any(flag.code == "self_harm_risk" for flag in red_flags)


def test_detect_red_flags_does_not_overfire_on_low_signal_text():
    case = make_case(
        transcript="Patient has mild chest wall soreness after exercise with no shortness of breath.",
        symptoms=["chest soreness"],
        severity="mild",
    )

    red_flags = detect_red_flags(case)

    assert red_flags == []
