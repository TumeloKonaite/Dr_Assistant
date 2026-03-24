from pathlib import Path
from unittest.mock import patch

from src.audio.loaders import load_chunks_from_folder


def test_load_chunks_from_folder_sorts_files_correctly():
    glob_results = [
        Path("chunk_0002.mp3"),
        Path("chunk_0000.mp3"),
        Path("chunk_0001.mp3"),
    ]
    with patch("pathlib.Path.glob", return_value=glob_results):
        files = load_chunks_from_folder("data/chunks")

    assert [f.name for f in files] == [
        "chunk_0000.mp3",
        "chunk_0001.mp3",
        "chunk_0002.mp3",
    ]


def test_load_chunks_from_folder_ignores_non_mp3_files():
    glob_results = [Path("chunk_0000.mp3")]
    with patch("pathlib.Path.glob", return_value=glob_results):
        files = load_chunks_from_folder("data/chunks")

    assert [f.name for f in files] == ["chunk_0000.mp3"]


def test_load_chunks_from_folder_returns_empty_list_for_empty_folder():
    with patch("pathlib.Path.glob", return_value=[]):
        files = load_chunks_from_folder("data/chunks")

    assert files == []
