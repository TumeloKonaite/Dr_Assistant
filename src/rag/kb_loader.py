from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import pandas as pd
import torch

from src.rag.config import KB_EMBEDDINGS_PT, KB_PKL, KB_TEXTS_PKL


def load_symptom2disease(csv_path: str):
    df = pd.read_csv(csv_path)
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    return df


def load_kb_artifacts(
    kb_path: str | Path = KB_PKL,
    kb_texts_path: str | Path = KB_TEXTS_PKL,
    kb_embeddings_path: str | Path = KB_EMBEDDINGS_PT,
) -> tuple[list[dict[str, Any]], list[str], torch.Tensor]:
    kb_path = Path(kb_path)
    kb_texts_path = Path(kb_texts_path)
    kb_embeddings_path = Path(kb_embeddings_path)

    missing_paths = [
        str(path)
        for path in (kb_path, kb_texts_path, kb_embeddings_path)
        if not path.exists()
    ]
    if missing_paths:
        raise FileNotFoundError(
            "Missing KB artifacts required for retrieval: "
            + ", ".join(missing_paths)
        )

    with kb_path.open("rb") as kb_file:
        kb = pickle.load(kb_file)

    with kb_texts_path.open("rb") as kb_texts_file:
        kb_texts = pickle.load(kb_texts_file)

    kb_embeddings = torch.load(kb_embeddings_path, map_location="cpu")

    if not isinstance(kb, list):
        raise ValueError("kb.pkl must contain a list of KB entries.")
    if not isinstance(kb_texts, list):
        raise ValueError("kb_texts.pkl must contain a list of KB texts.")
    if not isinstance(kb_embeddings, torch.Tensor):
        raise ValueError("kb_embeddings.pt must contain a torch.Tensor.")
    if kb_embeddings.ndim != 2:
        raise ValueError("kb_embeddings.pt must contain a 2D tensor.")
    if len(kb) != len(kb_texts):
        raise ValueError("kb.pkl and kb_texts.pkl must have the same length.")
    if len(kb) != kb_embeddings.shape[0]:
        raise ValueError(
            "Number of KB entries must match the number of embedding rows."
        )

    return kb, kb_texts, kb_embeddings
