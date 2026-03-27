from pathlib import Path

import pandas as pd


def load_symptom2disease(csv_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return df.drop(columns=["Unnamed: 0"], errors="ignore")
