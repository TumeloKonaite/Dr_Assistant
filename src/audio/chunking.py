from pathlib import Path
from moviepy import AudioFileClip

from src.contracts.chunk import Chunk


def chunk_audio(
    input_file: str,
    output_dir: str = "data/chunks",
    chunk_length: int = 30,
    overlap: int = 3,
) -> list[Chunk]:
    if overlap >= chunk_length:
        raise ValueError("overlap must be smaller than chunk_length")

    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    audio = AudioFileClip(str(input_path))
    duration = audio.duration
    step = chunk_length - overlap
    chunks: list[Chunk] = []

    try:
        start = 0.0
        idx = 0

        while start < duration:
            end = min(start + chunk_length, duration)
            chunk_path = out_dir / f"chunk_{idx:04d}.mp3"

            audio.subclipped(start, end).write_audiofile(
                str(chunk_path),
                codec="mp3",
                bitrate="64k",
                logger=None,
            )

            chunks.append(Chunk(idx, str(chunk_path), start, end))
            start += step
            idx += 1
    finally:
        audio.close()

    return chunks