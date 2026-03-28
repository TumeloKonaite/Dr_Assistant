from __future__ import annotations

import re


NOISE_MARKERS = (
    "[noise]",
    "[music]",
    "[inaudible]",
    "[silence]",
)


def normalize_transcript_text(text: str, speaker_separation: bool = False) -> str:
    """
    Apply conservative cleanup to ASR output without rewriting content.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()

    for marker in NOISE_MARKERS:
        cleaned = re.sub(re.escape(marker), "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]*\n[ \t]*", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    if speaker_separation:
        lines = [line.rstrip() for line in cleaned.splitlines()]
    else:
        lines = [line.strip() for line in cleaned.splitlines()]

    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned
