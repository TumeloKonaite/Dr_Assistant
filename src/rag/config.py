from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_INPUT_DIR = PROJECT_ROOT / "data" / "input"
DATA_OUTPUT_DIR = PROJECT_ROOT / "data" / "output"

SYMPTOM2DISEASE_CSV = DATA_INPUT_DIR / "Symptom2Disease.csv"

KB_PKL = DATA_OUTPUT_DIR / "kb.pkl"
KB_TEXTS_PKL = DATA_OUTPUT_DIR / "kb_texts.pkl"
KB_EMBEDDINGS_PT = DATA_OUTPUT_DIR / "kb_embeddings.pt"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
