from __future__ import annotations

import pytest

from src.utils.runtime_dependencies import validate_runtime_dependencies


def test_validate_runtime_dependencies_passes_when_all_tools_are_available(
    monkeypatch,
):
    monkeypatch.setattr(
        "src.utils.runtime_dependencies.shutil.which",
        lambda executable_name: f"C:/tools/{executable_name}.exe",
    )

    validate_runtime_dependencies()


def test_validate_runtime_dependencies_raises_clear_message_for_ffmpeg(
    monkeypatch,
):
    def fake_which(executable_name: str) -> str | None:
        if executable_name == "ffmpeg":
            return None
        return f"C:/tools/{executable_name}.exe"

    monkeypatch.setattr(
        "src.utils.runtime_dependencies.shutil.which",
        fake_which,
    )

    with pytest.raises(RuntimeError, match="ffmpeg is required"):
        validate_runtime_dependencies()
