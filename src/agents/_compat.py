from __future__ import annotations

from typing import Any, Callable

try:
    from agents import Agent, function_tool
except ImportError:
    class Agent:  # pragma: no cover - simple fallback for local testing
        def __init__(
            self,
            *,
            name: str,
            instructions: str,
            tools: list[Callable[..., Any]] | None = None,
            model: str | None = None,
        ) -> None:
            self.name = name
            self.instructions = instructions
            self.tools = tools or []
            self.model = model


    def function_tool(func: Callable[..., Any]) -> Callable[..., Any]:
        return func
