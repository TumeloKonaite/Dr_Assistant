from src.contracts.transcript import TranscriptChunk


def merge_transcripts(results: list[TranscriptChunk]) -> str:
    results = sorted(results, key=lambda x: x.index)
    return "\n".join(r.text.strip() for r in results)