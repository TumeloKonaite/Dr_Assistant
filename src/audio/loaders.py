from pathlib import Path


def load_chunks_from_folder(folder_path: str) -> list[Path]:
    folder = Path(folder_path)
    return sorted(
        folder.glob("*.mp3"),
        key=lambda x: int(x.stem.split("_")[-1])
    )