from __future__ import annotations

from src.contracts.consultation import ConsultationCase
from src.rag.query_builder import build_case_query
from src.tools.illness_retrieval_tool import retrieve_conditions


def main() -> None:
    sample_case = ConsultationCase(
        chief_complaint="Headache",
        symptoms=["fever", "nausea", "fatigue"],
        duration="3 days",
        transcript="Patient reports headache with fever, nausea, and fatigue for three days.",
    )

    query = build_case_query(sample_case)
    results = retrieve_conditions(sample_case, top_k=5)

    print("=== CASE ===")
    print(f"Chief complaint: {sample_case.chief_complaint}")
    print(f"Symptoms: {', '.join(sample_case.symptoms)}")
    print(f"Duration: {sample_case.duration}")
    print()

    print("=== QUERY ===")
    print(query)
    print()

    print("=== TOP CONDITIONS ===")
    for index, item in enumerate(results, start=1):
        print(f"{index}. {item.name:<25} score={item.score:.4f}")
        print(f"   Description: {item.description}")
        if item.matched_symptoms:
            print(f"   Matched symptoms: {', '.join(item.matched_symptoms)}")
        print()


if __name__ == "__main__":
    main()
