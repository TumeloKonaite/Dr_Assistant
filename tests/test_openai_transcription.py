from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, mock_open, patch

from src.providers.openai_transcription import transcribe_chunks


def test_transcribe_chunks_returns_expected_results():
    chunk_files = [
        Path("chunk_0000.mp3"),
        Path("chunk_0001.mp3"),
    ]

    fake_responses = [
        SimpleNamespace(text="Hello"),
        SimpleNamespace(text="world"),
    ]
    fake_client = SimpleNamespace(
        audio=SimpleNamespace(
            transcriptions=SimpleNamespace(create=Mock(side_effect=fake_responses)),
        )
    )

    with patch(
        "src.providers.openai_transcription.get_client",
        return_value=fake_client,
    ), patch("builtins.open", mock_open(read_data=b"fake_audio")):
        results = transcribe_chunks(chunk_files)

    assert len(results) == 2
    assert results[0].index == 0
    assert results[0].file == "chunk_0000.mp3"
    assert results[0].text == "Hello"

    assert results[1].index == 1
    assert results[1].file == "chunk_0001.mp3"
    assert results[1].text == "world"

    assert fake_client.audio.transcriptions.create.call_count == 2
