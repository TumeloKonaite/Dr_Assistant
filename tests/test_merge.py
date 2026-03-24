from src.audio.merge import merge_transcripts
from src.contracts.transcript import TranscriptChunk


def test_merge_transcripts_merges_in_index_order():
    results = [
        TranscriptChunk(index=1, file="chunk_0001.mp3", text="world"),
        TranscriptChunk(index=0, file="chunk_0000.mp3", text="Hello"),
    ]

    merged = merge_transcripts(results)

    assert merged == "Hello\nworld"


def test_merge_transcripts_strips_whitespace():
    results = [
        TranscriptChunk(index=0, file="chunk_0000.mp3", text="  Hello  "),
        TranscriptChunk(index=1, file="chunk_0001.mp3", text="\nworld\n"),
    ]

    merged = merge_transcripts(results)

    assert merged == "Hello\nworld"


def test_merge_transcripts_handles_empty_list():
    merged = merge_transcripts([])
    assert merged == ""