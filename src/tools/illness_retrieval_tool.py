from __future__ import annotations

from functools import lru_cache

import torch

from src.contracts.consultation import ConsultationCase, RetrievedCondition
from src.rag.config import EMBEDDING_MODEL_NAME
from src.rag.embedder import embed_texts, load_embedding_model
from src.rag.kb_loader import load_kb_artifacts
from src.rag.query_builder import build_case_query
from src.rag.retriever import retrieve_top_conditions


@lru_cache(maxsize=1)
def _get_embedding_model():
    return load_embedding_model(EMBEDDING_MODEL_NAME)


def _embed_single_query(query: str) -> torch.Tensor:
    embeddings = embed_texts(_get_embedding_model(), [query])

    if not isinstance(embeddings, torch.Tensor):
        embeddings = torch.as_tensor(embeddings, dtype=torch.float32)

    if embeddings.ndim != 2 or embeddings.shape[0] != 1:
        raise ValueError("embed_texts(model, [query]) must return a [1, dim] tensor.")

    return embeddings[0]


def retrieve_conditions(
    case: ConsultationCase,
    top_k: int = 5,
) -> list[RetrievedCondition]:
    query = build_case_query(case)
    kb, _, kb_embeddings = load_kb_artifacts()

    return retrieve_top_conditions(
        query=query,
        kb=kb,
        kb_embeddings=kb_embeddings,
        embed_query=_embed_single_query,
        top_k=top_k,
    )
