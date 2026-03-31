from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from src.pipelines.legacy_transcription_pipeline import (
    run_legacy_transcription_pipeline,
)
from src.pipelines.post_consultation_pipeline import (
    build_output_dir_path,
    run_post_consultation_pipeline,
)
from src.rag.build_kb_artifacts import main as build_kb_artifacts_main


def load_doctor_notes(notes_path: str) -> str:
    path = Path(notes_path)

    if not path.exists():
        raise FileNotFoundError(f"Doctor notes file does not exist: {notes_path}")

    if not path.is_file():
        raise ValueError(f"Doctor notes path is not a file: {notes_path}")

    return path.read_text(encoding="utf-8")


def _add_analyze_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--file", required=True, help="Path to the consultation media file"
    )
    parser.add_argument(
        "--notes", required=True, help="Path to the doctor notes text file"
    )
    parser.add_argument(
        "--output-dir",
        help="Directory where pipeline artifacts should be written",
    )


def _add_transcribe_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", required=True, help="Path to the input media file")
    parser.add_argument(
        "--output-dir",
        default="data/output",
        help="Directory where transcription artifacts should be written",
    )


def _handle_analyze(
    args: argparse.Namespace,
    *,
    build_output_dir_path_fn: Callable[[], Path] | None = None,
    load_doctor_notes_fn: Callable[[str], str] | None = None,
    run_post_consultation_pipeline_fn: Callable[..., object] | None = None,
) -> int:
    build_output_dir_path_fn = build_output_dir_path_fn or build_output_dir_path
    load_doctor_notes_fn = load_doctor_notes_fn or load_doctor_notes
    run_post_consultation_pipeline_fn = (
        run_post_consultation_pipeline_fn or run_post_consultation_pipeline
    )
    resolved_output_dir = (
        Path(args.output_dir) if args.output_dir else build_output_dir_path_fn()
    )

    try:
        doctor_notes = load_doctor_notes_fn(args.notes)
        bundle = run_post_consultation_pipeline_fn(
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


def _handle_transcribe(
    args: argparse.Namespace,
    *,
    run_transcription_pipeline_fn: Callable[..., str] | None = None,
) -> int:
    run_transcription_pipeline_fn = (
        run_transcription_pipeline_fn or run_legacy_transcription_pipeline
    )
    try:
        run_transcription_pipeline_fn(args.input, output_dir=args.output_dir)
        return 0
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1


def _handle_build_kb(
    *,
    build_kb_artifacts_main_fn: Callable[[], None] | None = None,
) -> int:
    build_kb_artifacts_main_fn = (
        build_kb_artifacts_main_fn or build_kb_artifacts_main
    )
    try:
        build_kb_artifacts_main_fn()
        return 0
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dr Assistant command line interface.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run the canonical post-consultation pipeline.",
    )
    _add_analyze_arguments(analyze_parser)

    transcribe_parser = subparsers.add_parser(
        "transcribe",
        help="Run the transcription-only pipeline.",
    )
    _add_transcribe_arguments(transcribe_parser)

    subparsers.add_parser(
        "build-kb",
        help="Build knowledge-base artifacts from the configured dataset.",
    )

    return parser


def run_analyze_command(
    argv: list[str] | None = None,
    *,
    build_output_dir_path_fn: Callable[[], Path] | None = None,
    load_doctor_notes_fn: Callable[[str], str] | None = None,
    run_post_consultation_pipeline_fn: Callable[..., object] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Run the canonical post-consultation pipeline."
    )
    _add_analyze_arguments(parser)
    args = parser.parse_args(argv)
    return _handle_analyze(
        args,
        build_output_dir_path_fn=build_output_dir_path_fn,
        load_doctor_notes_fn=load_doctor_notes_fn,
        run_post_consultation_pipeline_fn=run_post_consultation_pipeline_fn,
    )


def run_transcribe_command(
    argv: list[str] | None = None,
    *,
    run_transcription_pipeline_fn: Callable[..., str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Run the transcription-only consultation pipeline."
    )
    _add_transcribe_arguments(parser)
    args = parser.parse_args(argv)
    return _handle_transcribe(
        args, run_transcription_pipeline_fn=run_transcription_pipeline_fn
    )


def run_build_kb_command(
    argv: list[str] | None = None,
    *,
    build_kb_artifacts_main_fn: Callable[[], None] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Build knowledge-base artifacts for retrieval."
    )
    parser.parse_args(argv)
    return _handle_build_kb(build_kb_artifacts_main_fn=build_kb_artifacts_main_fn)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _handle_analyze(args)
    if args.command == "transcribe":
        return _handle_transcribe(args)
    if args.command == "build-kb":
        return _handle_build_kb()

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
