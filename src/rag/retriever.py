from __future__ import annotations

from collections.abc import Callable
from typing import Any

import torch
import torch.nn.functional as F

from src.contracts.consultation import RetrievedCondition


EmbedQueryFn = Callable[[str], torch.Tensor]


def _normalize_query_embedding(query_embedding: torch.Tensor) -> torch.Tensor:
    if query_embedding.ndim == 1:
        query_embedding = query_embedding.unsqueeze(0)

    if query_embedding.ndim != 2 or query_embedding.shape[0] != 1:
        raise ValueError("Query embedding must have shape [dim] or [1, dim].")

    return F.normalize(query_embedding, p=2, dim=1)


def _entry_name(entry: dict[str, Any]) -> str:
    name = entry.get("name") or entry.get("disease")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("KB entry is missing a usable disease name.")
    return name.strip()


def _entry_description(entry: dict[str, Any]) -> str:
    description = entry.get("description")
    if isinstance(description, str) and description.strip():
        return description.strip()

    name = _entry_name(entry)
    return f"{name} is a possible condition represented in this knowledge base."


def _entry_symptoms(entry: dict[str, Any]) -> list[str]:
    symptoms = entry.get("symptoms", [])
    if not isinstance(symptoms, list):
        return []

    return [symptom.strip() for symptom in symptoms if isinstance(symptom, str) and symptom.strip()]


def retrieve_top_conditions(
    *,
    query: str,
    kb: list[dict[str, Any]],
    kb_embeddings: torch.Tensor,
    embed_query: EmbedQueryFn,
    top_k: int = 5,
) -> list[RetrievedCondition]:
    if not query.strip():
        raise ValueError("Query must not be empty.")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")
    if top_k > 10:
        raise ValueError("top_k must be less than or equal to 10.")
    if not kb:
        return []
    if kb_embeddings.ndim != 2:
        raise ValueError("KB embeddings must be a 2D tensor.")
    if kb_embeddings.shape[0] != len(kb):
        raise ValueError("KB size and embedding rows must match.")

    query_embedding = _normalize_query_embedding(embed_query(query))
    normalized_kb_embeddings = F.normalize(kb_embeddings, p=2, dim=1)
    similarity_scores = torch.matmul(
        normalized_kb_embeddings,
        query_embedding.T,
    ).squeeze(1)

    ranked_indices = sorted(
        range(len(kb)),
        key=lambda index: (-float(similarity_scores[index].item()), index),
    )[: min(top_k, len(kb))]

    return [
        RetrievedCondition(
            name=_entry_name(kb[index]),
            description=_entry_description(kb[index]),
            matched_symptoms=_entry_symptoms(kb[index]),
            score=float(similarity_scores[index].item()),
        )
        for index in ranked_indices
    ]
