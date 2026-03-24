from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    path: str
    start: float
    end: float