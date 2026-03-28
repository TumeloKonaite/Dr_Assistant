from pathlib import Path

import pytest

from src.tools.transcription_tool import main, transcribe_consultation


def test_transcribe_consultation_raises_for_missing_file():
    with pytest.raises(FileNotFoundError, match="Input file does not exist"):
        transcribe_consultation("missing-input.mp4")


def test_transcribe_consultation_raises_for_unsupported_file():
    input_file = Path("README.md")

    with pytest.raises(ValueError, match="Unsupported file type"):
        transcribe_consultation(str(input_file))


def test_transcribe_consultation_returns_cleaned_text(monkeypatch):
    def fake_pipeline(file_path: str) -> str:
        assert file_path == "input.mp4"
        return "Patient has fever.   [noise]\n\n\nCough started yesterday."

    monkeypatch.setattr(
        "src.tools.transcription_tool.run_transcription_pipeline_for_media",
        fake_pipeline,
    )

    result = transcribe_consultation("input.mp4")

    assert result == "Patient has fever.\n\nCough started yesterday."


def test_transcribe_consultation_propagates_pipeline_errors(monkeypatch):
    def fake_pipeline(file_path: str) -> str:
        raise RuntimeError("backend unavailable")

    monkeypatch.setattr(
        "src.tools.transcription_tool.run_transcription_pipeline_for_media",
        fake_pipeline,
    )

    with pytest.raises(RuntimeError, match="backend unavailable"):
        transcribe_consultation("input.mp4")


def test_main_prints_transcript_to_stdout(monkeypatch, capsys):
    monkeypatch.setattr(
        "src.tools.transcription_tool.transcribe_consultation",
        lambda file_path: "Clean transcript",
    )

    exit_code = main(["input.mp4"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "Clean transcript\n"
    assert captured.err == ""


def test_main_prints_errors_to_stderr(monkeypatch, capsys):
    def fake_transcribe(file_path: str) -> str:
        raise FileNotFoundError("Input file does not exist: input.mp4")

    monkeypatch.setattr(
        "src.tools.transcription_tool.transcribe_consultation",
        fake_transcribe,
    )

    exit_code = main(["input.mp4"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Input file does not exist: input.mp4" in captured.err
