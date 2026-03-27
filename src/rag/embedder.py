from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer


def load_embedding_model(model_name: str) -> SentenceTransformer:
    try:
        return SentenceTransformer(model_name)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load embedding model '{model_name}'. "
            "Ensure it is already cached locally or run the pipeline with internet access "
            "so SentenceTransformer can download it on first use."
        ) from exc


def embed_texts(model: SentenceTransformer, texts: list[str]) -> torch.Tensor:
    return model.encode(
        texts,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )


def save_torch_tensor(tensor: torch.Tensor, path: str | Path) -> None:
    torch.save(tensor, path)
