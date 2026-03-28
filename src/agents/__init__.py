__all__ = [
    "case_builder_agent",
    "retrieval_agent",
    "differential_agent",
    "planner_agent",
]


def __getattr__(name: str):
    if name == "case_builder_agent":
        from src.agents.case_builder_agent import case_builder_agent

        return case_builder_agent
    if name == "retrieval_agent":
        from src.agents.retrieval_agent import retrieval_agent

        return retrieval_agent
    if name == "differential_agent":
        from src.agents.differential_agent import differential_agent

        return differential_agent
    if name == "planner_agent":
        from src.agents.planner_agent import planner_agent

        return planner_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
