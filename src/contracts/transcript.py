from dataclasses import dataclass


@dataclass
class TranscriptChunk:
    index: int
    file: str
    text: str