from pathlib import Path
from openai import OpenAI

from src.contracts.transcript import TranscriptChunk


client = OpenAI()


def transcribe_chunks(chunk_files: list[Path]) -> list[TranscriptChunk]:
    results: list[TranscriptChunk] = []

    for i, file_path in enumerate(chunk_files):
        print(f"Transcribing {file_path.name}...")

        with open(file_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f
            )

        results.append(
            TranscriptChunk(
                index=i,
                file=file_path.name,
                text=transcript.text
            )
        )

    return results