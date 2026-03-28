import pytest

from src.utils.transcript_cleaning import normalize_transcript_text


def test_normalize_transcript_text_removes_noise_markers():
    raw = "Patient reports headache. [noise] Also has nausea. [inaudible]"

    cleaned = normalize_transcript_text(raw)

    assert "[noise]" not in cleaned.lower()
    assert "[inaudible]" not in cleaned.lower()
    assert "Patient reports headache." in cleaned
    assert "Also has nausea." in cleaned


def test_normalize_transcript_text_collapses_extra_spaces():
    raw = "Patient   has    had pain   for two days."

    cleaned = normalize_transcript_text(raw)

    assert cleaned == "Patient has had pain for two days."


def test_normalize_transcript_text_collapses_blank_lines():
    raw = "Line one.\n\n\n\nLine two."

    cleaned = normalize_transcript_text(raw)

    assert cleaned == "Line one.\n\nLine two."


def test_normalize_transcript_text_normalizes_punctuation_spacing():
    raw = "Patient reports nausea , dizziness ; and fatigue ."

    cleaned = normalize_transcript_text(raw)

    assert cleaned == "Patient reports nausea, dizziness; and fatigue."


def test_normalize_transcript_text_raises_for_non_string():
    with pytest.raises(TypeError, match="text must be a string"):
        normalize_transcript_text(None)  # type: ignore[arg-type]
