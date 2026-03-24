from pathlib import Path

from src.audio.chunking import chunk_audio
from src.audio.normalize import normalize_audio
from src.pipelines.transcribe_chunks import run_transcription_pipeline


def _clear_existing_chunks(chunks_dir: Path) -> None:
    for chunk_file in chunks_dir.glob("*.mp3"):
        chunk_file.unlink()


def run_full_pipeline(input_file: str, output_dir: str = "data/output") -> str:
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_path = Path(output_dir)
    chunks_dir = output_path / "chunks"
    normalized_path = output_path / f"{input_path.stem}_normalized.wav"
    transcript_file = output_path / f"{input_path.stem}_transcript.txt"

    output_path.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    _clear_existing_chunks(chunks_dir)

    chunk_source = str(input_path)

    print("Normalizing audio...")
    try:
        chunk_source = normalize_audio(
            str(input_path),
            output_file=str(normalized_path),
        )
    except RuntimeError as exc:
        if "No space left on device" not in str(exc):
            raise
        print("Normalization skipped: insufficient disk space for WAV output. Chunking source media directly...")

    print("Chunking audio...")
    chunk_audio(chunk_source, output_dir=str(chunks_dir))

    print("Transcribing...")
    transcript = run_transcription_pipeline(str(chunks_dir))

    transcript_file.write_text(transcript, encoding="utf-8")
    print(f"Done. Transcript saved to {transcript_file}")

    return transcript
