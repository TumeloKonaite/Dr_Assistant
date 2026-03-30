from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.pipelines.post_consultation_pipeline import (
    build_output_dir_path,
    run_post_consultation_pipeline,
)


def load_doctor_notes(notes_path: str) -> str:
    path = Path(notes_path)

    if not path.exists():
        raise FileNotFoundError(f"Doctor notes file does not exist: {notes_path}")

    if not path.is_file():
        raise ValueError(f"Doctor notes path is not a file: {notes_path}")

    return path.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the canonical post-consultation pipeline."
    )
    parser.add_argument("--file", required=True, help="Path to the consultation media file")
    parser.add_argument("--notes", required=True, help="Path to the doctor notes text file")
    parser.add_argument(
        "--output-dir",
        help="Directory where pipeline artifacts should be written",
    )
    args = parser.parse_args(argv)

    resolved_output_dir = Path(args.output_dir) if args.output_dir else build_output_dir_path()

    try:
        doctor_notes = load_doctor_notes(args.notes)
        bundle = run_post_consultation_pipeline(
            file_path=args.file,
            doctor_notes=doctor_notes,
            output_dir=str(resolved_output_dir),
        )
        print("Pipeline completed successfully.")
        print(f"Outputs saved to {resolved_output_dir}")
        print(f"Chief complaint: {bundle.case.chief_complaint}")
        print(f"Differentials generated: {len(bundle.differentials)}")
        return 0
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
