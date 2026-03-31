from src.cli import run_transcribe_command
from src.pipelines.legacy_transcription_pipeline import (
    run_legacy_transcription_pipeline,
)


def main(argv: list[str] | None = None) -> int:
    return run_transcribe_command(
        argv,
        run_transcription_pipeline_fn=run_legacy_transcription_pipeline,
    )


if __name__ == "__main__":
    raise SystemExit(main())
