from src.audio import loaders, merge
from src.providers import openai_transcription


def run_transcription_pipeline(chunks_dir: str) -> str:
    chunk_files = loaders.load_chunks_from_folder(chunks_dir)
    results = openai_transcription.transcribe_chunks(chunk_files)
    return merge.merge_transcripts(results)
