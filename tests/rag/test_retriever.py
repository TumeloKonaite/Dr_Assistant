import torch

from src.rag.retriever import retrieve_top_conditions


def test_retrieve_top_conditions_returns_sorted_results():
    kb = [
        {
            "name": "Flu",
            "description": "Flu description",
            "symptoms": ["fever", "fatigue"],
        },
        {
            "name": "Migraine",
            "description": "Migraine description",
            "symptoms": ["headache", "nausea"],
        },
        {
            "name": "Cold",
            "description": "Cold description",
            "symptoms": ["cough", "sore throat"],
        },
    ]

    kb_embeddings = torch.tensor(
        [
            [1.0, 0.0],
            [0.8, 0.2],
            [0.0, 1.0],
        ],
        dtype=torch.float32,
    )

    def fake_embed_query(_: str) -> torch.Tensor:
        return torch.tensor([1.0, 0.0], dtype=torch.float32)

    results = retrieve_top_conditions(
        query="headache fever",
        kb=kb,
        kb_embeddings=kb_embeddings,
        embed_query=fake_embed_query,
        top_k=2,
    )

    assert len(results) == 2
    assert results[0].name == "Flu"
    assert results[1].name == "Migraine"
    assert results[0].score >= results[1].score


def test_retrieve_top_conditions_handles_top_k_larger_than_kb():
    kb = [
        {"name": "Flu", "description": "Flu description", "symptoms": ["fever"]},
    ]
    kb_embeddings = torch.tensor([[1.0, 0.0]], dtype=torch.float32)

    def fake_embed_query(_: str) -> torch.Tensor:
        return torch.tensor([1.0, 0.0], dtype=torch.float32)

    results = retrieve_top_conditions(
        query="fever",
        kb=kb,
        kb_embeddings=kb_embeddings,
        embed_query=fake_embed_query,
        top_k=10,
    )

    assert len(results) == 1
    assert results[0].name == "Flu"


def test_retrieve_top_conditions_accepts_disease_key_from_current_kb_shape():
    kb = [
        {
            "disease": "influenza",
            "description": "Influenza is a possible condition represented in this knowledge base.",
            "symptoms": [],
        },
        {
            "disease": "migraine",
            "description": "Migraine is a possible condition represented in this knowledge base.",
            "symptoms": [],
        },
    ]
    kb_embeddings = torch.tensor([[1.0, 0.0], [0.0, 1.0]], dtype=torch.float32)

    def fake_embed_query(_: str) -> torch.Tensor:
        return torch.tensor([1.0, 0.0], dtype=torch.float32)

    results = retrieve_top_conditions(
        query="fever headache",
        kb=kb,
        kb_embeddings=kb_embeddings,
        embed_query=fake_embed_query,
        top_k=2,
    )

    assert [item.name for item in results] == ["influenza", "migraine"]
