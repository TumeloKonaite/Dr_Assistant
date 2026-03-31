from __future__ import annotations

import shutil


RUNTIME_DEPENDENCIES: tuple[tuple[str, str], ...] = (
    ("ffmpeg", "ffmpeg"),
)


def validate_runtime_dependencies() -> None:
    missing = [
        display_name
        for executable_name, display_name in RUNTIME_DEPENDENCIES
        if shutil.which(executable_name) is None
    ]

    if not missing:
        return

    if len(missing) == 1:
        message = f"{missing[0]} is required to be installed and available on PATH."
    else:
        missing_list = ", ".join(missing)
        message = (
            f"The following runtime dependencies are required to be installed and "
            f"available on PATH: {missing_list}."
        )

    raise RuntimeError(message)
