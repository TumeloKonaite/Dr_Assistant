from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from src.audio.chunking import chunk_audio
from src.audio.merge import merge_transcripts
from src.audio.normalize import normalize_audio
from src.providers.openai_transcription import transcribe_chunks


SUPPORTED_EXTENSIONS = {
    ".aac",
    ".avi",
    ".flac",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".wav",
    ".webm",
}


def validate_input_file(file_path: str) -> Path:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {file_path}")

    if not path.is_file():
        raise ValueError(f"Input path is not a file: {file_path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file type: {path.suffix}. Supported types: {supported}"
        )

    return path


def _prepare_chunk_source(input_path: Path, workspace_dir: Path) -> str:
    normalized_path = workspace_dir / f"{input_path.stem}_normalized.wav"

    try:
        return normalize_audio(str(input_path), output_file=str(normalized_path))
    except RuntimeError as exc:
        if "No space left on device" not in str(exc):
            raise
        return str(input_path)


def run_transcription_pipeline_for_media(file_path: str) -> str:
    input_path = validate_input_file(file_path)

    with TemporaryDirectory(prefix="dr_assistant_transcription_") as temp_dir:
        workspace_dir = Path(temp_dir)
        chunks_dir = workspace_dir / "chunks"

        chunk_source = _prepare_chunk_source(input_path, workspace_dir)
        chunks = chunk_audio(chunk_source, output_dir=str(chunks_dir))
        chunk_files = [Path(chunk.path) for chunk in chunks]
        transcript_chunks = transcribe_chunks(chunk_files)
        merged_transcript = merge_transcripts(transcript_chunks)

    if not isinstance(merged_transcript, str):
        raise TypeError("Merged transcript must be a string")

    return merged_transcript.strip()
