from __future__ import annotations

from src.cli import run_build_kb_command
from src.pipelines.build_kb_artifacts import main as build_kb_artifacts_main


def main(argv: list[str] | None = None) -> int:
    return run_build_kb_command(
        argv,
        build_kb_artifacts_main_fn=build_kb_artifacts_main,
    )


if __name__ == "__main__":
    raise SystemExit(main())
