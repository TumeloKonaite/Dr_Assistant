from pathlib import Path
from unittest.mock import patch

import pytest

from src.contracts.transcript import TranscriptChunk
from src.pipelines.legacy_transcription_pipeline import (
    run_legacy_transcription_pipeline,
)
from src.pipelines.transcribe_chunks import run_transcription_pipeline


def test_run_transcription_pipeline():
    fake_chunks = [
        Path("chunk_0000.mp3"),
        Path("chunk_0001.mp3"),
    ]

    fake_results = [
        TranscriptChunk(index=0, file="chunk_0000.mp3", text="Hello"),
        TranscriptChunk(index=1, file="chunk_0001.mp3", text="world"),
    ]

    with (
        patch(
            "src.pipelines.transcribe_chunks.loaders.load_chunks_from_folder",
            return_value=fake_chunks,
        ) as mock_load,
        patch(
            "src.pipelines.transcribe_chunks.openai_transcription.transcribe_chunks",
            return_value=fake_results,
        ) as mock_transcribe,
        patch(
            "src.pipelines.transcribe_chunks.merge.merge_transcripts",
            return_value="Hello\nworld",
        ) as mock_merge,
    ):
        result = run_transcription_pipeline("data/chunks")

    assert result == "Hello\nworld"
    mock_load.assert_called_once_with("data/chunks")
    mock_transcribe.assert_called_once_with(fake_chunks)
    mock_merge.assert_called_once_with(fake_results)


def test_run_transcription_pipeline_with_no_chunks():
    with (
        patch(
            "src.pipelines.transcribe_chunks.loaders.load_chunks_from_folder",
            return_value=[],
        ) as mock_load,
        patch(
            "src.pipelines.transcribe_chunks.openai_transcription.transcribe_chunks",
            return_value=[],
        ) as mock_transcribe,
        patch(
            "src.pipelines.transcribe_chunks.merge.merge_transcripts",
            return_value="",
        ) as mock_merge,
    ):
        result = run_transcription_pipeline("data/chunks")

    assert result == ""
    mock_load.assert_called_once_with("data/chunks")
    mock_transcribe.assert_called_once_with([])
    mock_merge.assert_called_once_with([])


def test_run_transcription_pipeline_raises_on_transcription_failure():
    with (
        patch(
            "src.pipelines.transcribe_chunks.loaders.load_chunks_from_folder",
            return_value=[Path("chunk_0000.mp3")],
        ),
        patch(
            "src.pipelines.transcribe_chunks.openai_transcription.transcribe_chunks",
            side_effect=RuntimeError("API error"),
        ),
    ):
        with pytest.raises(RuntimeError, match="API error"):
            run_transcription_pipeline("data/chunks")


def test_run_legacy_transcription_pipeline_writes_outputs_under_output_dir():
    with (
        patch(
            "src.pipelines.legacy_transcription_pipeline.Path.exists",
            return_value=True,
        ),
        patch(
            "src.pipelines.legacy_transcription_pipeline.Path.mkdir",
        ),
        patch(
            "src.pipelines.legacy_transcription_pipeline.Path.write_text",
        ) as mock_write_text,
        patch(
            "src.pipelines.legacy_transcription_pipeline._clear_existing_chunks",
        ) as mock_clear,
        patch(
            "src.pipelines.legacy_transcription_pipeline.normalize_audio",
            return_value="data/output/meeting_normalized.wav",
        ) as mock_normalize,
        patch(
            "src.pipelines.legacy_transcription_pipeline.chunk_audio",
        ) as mock_chunk,
        patch(
            "src.pipelines.legacy_transcription_pipeline.run_transcription_pipeline",
            return_value="hello world",
        ) as mock_transcribe,
    ):
        result = run_legacy_transcription_pipeline(
            "meeting.mp4", output_dir="data/output"
        )

    assert result == "hello world"
    mock_clear.assert_called_once()
    mock_normalize.assert_called_once_with(
        "meeting.mp4",
        output_file=str(Path("data/output/meeting_normalized.wav")),
    )
    mock_chunk.assert_called_once_with(
        "data/output/meeting_normalized.wav",
        output_dir=str(Path("data/output/chunks")),
    )
    mock_transcribe.assert_called_once_with(str(Path("data/output/chunks")))
    mock_write_text.assert_called_once_with("hello world", encoding="utf-8")


def test_run_legacy_transcription_pipeline_falls_back_to_source_media_on_disk_space_error():
    with (
        patch(
            "src.pipelines.legacy_transcription_pipeline.Path.exists",
            return_value=True,
        ),
        patch(
            "src.pipelines.legacy_transcription_pipeline.Path.mkdir",
        ),
        patch(
            "src.pipelines.legacy_transcription_pipeline.Path.write_text",
        ),
        patch(
            "src.pipelines.legacy_transcription_pipeline._clear_existing_chunks",
        ),
        patch(
            "src.pipelines.legacy_transcription_pipeline.normalize_audio",
            side_effect=RuntimeError(
                "FFmpeg normalization failed:\nNo space left on device"
            ),
        ),
        patch(
            "src.pipelines.legacy_transcription_pipeline.chunk_audio",
        ) as mock_chunk,
        patch(
            "src.pipelines.legacy_transcription_pipeline.run_transcription_pipeline",
            return_value="fallback ok",
        ),
    ):
        result = run_legacy_transcription_pipeline(
            "meeting.mp4", output_dir="data/output"
        )

    assert result == "fallback ok"
    mock_chunk.assert_called_once_with(
        "meeting.mp4",
        output_dir=str(Path("data/output/chunks")),
    )
