from __future__ import annotations

from src.cli import load_doctor_notes, run_analyze_command
from src.pipelines.post_consultation_pipeline import (
    build_output_dir_path,
    run_post_consultation_pipeline,
)


def main(argv: list[str] | None = None) -> int:
    return run_analyze_command(
        argv,
        build_output_dir_path_fn=build_output_dir_path,
        load_doctor_notes_fn=load_doctor_notes,
        run_post_consultation_pipeline_fn=run_post_consultation_pipeline,
    )


if __name__ == "__main__":
    raise SystemExit(main())
