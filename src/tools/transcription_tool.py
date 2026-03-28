from __future__ import annotations

import argparse
import sys

from src.pipelines.transcription_pipeline import run_transcription_pipeline_for_media
from src.utils.transcript_cleaning import normalize_transcript_text


def transcribe_consultation(file_path: str) -> str:
    raw_transcript = run_transcription_pipeline_for_media(file_path)
    return normalize_transcript_text(raw_transcript)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe a consultation audio/video file."
    )
    parser.add_argument("file_path", help="Path to the input audio/video file")
    args = parser.parse_args(argv)

    try:
        transcript = transcribe_consultation(args.file_path)
        print(transcript)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
