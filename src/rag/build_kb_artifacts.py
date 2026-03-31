import pickle

from src.rag.config import (
    DATA_OUTPUT_DIR,
    KB_EMBEDDINGS_PT,
    KB_PKL,
    KB_TEXTS_PKL,
    EMBEDDING_MODEL_NAME,
    SYMPTOM2DISEASE_CSV,
)
from src.rag.embedder import embed_texts, load_embedding_model, save_torch_tensor
from src.rag.kb_builder import build_kb_from_symptom2disease, build_kb_texts
from src.rag.kb_loader import load_symptom2disease


def save_pickle(obj, path) -> None:
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def main():
    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading dataset...")
    df = load_symptom2disease(SYMPTOM2DISEASE_CSV)

    print("Building knowledge base...")
    kb = build_kb_from_symptom2disease(df)

    print("Building embedding texts...")
    kb_texts = build_kb_texts(kb)

    print("Loading embedding model...")
    model = load_embedding_model(EMBEDDING_MODEL_NAME)

    print("Generating embeddings...")
    kb_embeddings = embed_texts(model, kb_texts)

    print("Saving artifacts...")
    save_pickle(kb, KB_PKL)
    save_pickle(kb_texts, KB_TEXTS_PKL)
    save_torch_tensor(kb_embeddings, KB_EMBEDDINGS_PT)

    print("Done.")
    print(f"KB entries: {len(kb)}")
    print(f"Saved: {KB_PKL}")
    print(f"Saved: {KB_TEXTS_PKL}")
    print(f"Saved: {KB_EMBEDDINGS_PT}")


if __name__ == "__main__":
    main()
