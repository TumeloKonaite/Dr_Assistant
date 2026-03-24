"""
Audio normalization module.

Handles:
- Extracting audio from video/audio files
- Converting to mono (1 channel)
- Resampling to 16kHz
- Volume normalization (loudnorm)
- Outputting WAV (PCM 16-bit)

This is the FIRST step in the transcription pipeline.
"""

import subprocess
from pathlib import Path


def normalize_audio(
    input_file: str,
    output_file: str | None = None,
    sample_rate: int = 16000,
    channels: int = 1,
    apply_loudnorm: bool = True,
) -> str:
    """
    Normalize audio for transcription.

    Args:
        input_file: Path to input video/audio file.
        output_file: Optional output path. Defaults to same directory with '_normalized.wav'.
        sample_rate: Target sample rate (default: 16000 Hz).
        channels: Number of audio channels (default: 1 = mono).
        apply_loudnorm: Whether to apply volume normalization.

    Returns:
        Path to normalized audio file.
    """
    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if output_file is None:
        output_file = input_path.with_name(f"{input_path.stem}_normalized.wav")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",  # overwrite output
        "-i", str(input_path),
        "-vn",  # remove video
        "-ac", str(channels),
        "-ar", str(sample_rate),
    ]

    if apply_loudnorm:
        cmd.extend(["-af", "loudnorm"])

    cmd.extend([
        "-acodec", "pcm_s16le",  # WAV 16-bit
        str(output_path)
    ])

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"FFmpeg normalization failed:\n{e.stderr.decode()}"
        )

    return str(output_path)


def is_media_file(file_path: str) -> bool:
    """
    Basic check for supported media types.
    """
    supported_extensions = {
        ".mp4", ".mov", ".avi", ".mkv",
        ".mp3", ".wav", ".aac", ".flac", ".ogg"
    }

    return Path(file_path).suffix.lower() in supported_extensions


if __name__ == "__main__":
    # Example usage (for quick testing)
    test_input = "data/input/sample.mp4"

    output = normalize_audio(test_input)
    print(f"Normalized audio saved to: {output}")