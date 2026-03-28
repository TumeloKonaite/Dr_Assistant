from pathlib import Path
from functools import lru_cache

from openai import OpenAI

from src.contracts.transcript import TranscriptChunk


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI()


def transcribe_chunks(chunk_files: list[Path]) -> list[TranscriptChunk]:
    results: list[TranscriptChunk] = []
    client = get_client()

    for i, file_path in enumerate(chunk_files):
        print(f"Transcribing {file_path.name}...")

        with open(file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f,
            )

        results.append(
            TranscriptChunk(
                index=i,
                file=file_path.name,
                text=transcript.text,
            )
        )

    return results
