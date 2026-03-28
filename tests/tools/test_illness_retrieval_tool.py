from unittest.mock import patch

import pytest
import torch

from src.contracts.consultation import ConsultationCase, RetrievedCondition
from src.tools.illness_retrieval_tool import retrieve_conditions


def test_retrieve_conditions_happy_path():
    case = ConsultationCase(
        chief_complaint="Headache",
        symptoms=["fever", "nausea"],
        duration="2 days",
        transcript="Patient reports headache with fever and nausea for two days.",
    )

    fake_kb = [
        {"name": "Flu", "description": "desc", "symptoms": ["fever"]},
    ]
    fake_embeddings = torch.tensor([[1.0, 0.0]], dtype=torch.float32)

    with patch(
        "src.tools.illness_retrieval_tool.build_case_query",
        return_value="query",
    ), patch(
        "src.tools.illness_retrieval_tool.load_kb_artifacts",
        return_value=(fake_kb, ["text"], fake_embeddings),
    ), patch(
        "src.tools.illness_retrieval_tool.retrieve_top_conditions"
    ) as mock_retrieve:
        mock_retrieve.return_value = [
            RetrievedCondition(
                name="Flu",
                description="desc",
                matched_symptoms=["fever"],
                score=0.9,
            )
        ]

        result = retrieve_conditions(case, top_k=5)

        assert len(result) == 1
        assert result[0].name == "Flu"
        mock_retrieve.assert_called_once_with(
            query="query",
            kb=fake_kb,
            kb_embeddings=fake_embeddings,
            embed_query=mock_retrieve.call_args.kwargs["embed_query"],
            top_k=5,
        )


def test_retrieve_conditions_propagates_missing_artifact_error():
    case = ConsultationCase(
        chief_complaint="Headache",
        symptoms=["fever"],
        duration="2 days",
        transcript="Patient reports headache with fever for two days.",
    )

    with patch(
        "src.tools.illness_retrieval_tool.load_kb_artifacts",
        side_effect=FileNotFoundError("missing artifacts"),
    ):
        with pytest.raises(FileNotFoundError, match="missing artifacts"):
            retrieve_conditions(case)
