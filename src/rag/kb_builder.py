from typing import Any


def build_kb_from_symptom2disease(df) -> list[dict[str, Any]]:
    kb: list[dict[str, Any]] = []

    for disease, group in df.groupby("label"):
        examples = group["text"].dropna().tolist()

        kb.append(
            {
                "id": f"disease_{str(disease).lower().replace(' ', '_')}",
                "disease": str(disease).lower(),
                "symptoms": [],
                "description": f"{disease} is a possible condition represented in this knowledge base.",
                "examples": examples[:10],
            }
        )

    return kb


def build_embedding_text(entry: dict[str, Any]) -> str:
    parts = [
        f"Disease: {entry['disease']}",
        f"Description: {entry['description']}",
    ]

    if entry.get("symptoms"):
        parts.append("Symptoms: " + ", ".join(entry["symptoms"][:20]))

    if entry.get("examples"):
        parts.append("Patient descriptions: " + " ".join(entry["examples"][:3]))

    return "\n".join(parts)


def build_kb_texts(kb: list[dict[str, Any]]) -> list[str]:
    return [build_embedding_text(entry) for entry in kb]
