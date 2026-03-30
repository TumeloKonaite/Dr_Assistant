
# 🩺 Dr_Assistant

[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-transcription%20%2B%20reasoning-412991?logo=openai&logoColor=white)](https://platform.openai.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-typed%20contracts-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](#-license)

Dr_Assistant is a modular transcription and post-consultation pipeline designed for clinical workflows.  
It converts audio/video consultations into clean transcripts and forms the foundation for downstream AI-powered medical reasoning (case extraction, retrieval, differential diagnosis, and documentation).

---

## 🚀 Overview

The current system focuses on **robust, reusable transcription** as the first stage of a larger clinical assistant pipeline.

### Core capabilities

- 🎧 Audio normalization using `ffmpeg`
- ✂️ Intelligent chunking with overlap using `moviepy`
- 🧠 High-quality transcription via OpenAI APIs
- 🔗 Deterministic transcript merging
- 📂 Structured output artifacts for downstream pipelines

---

## 🧱 Architecture

The pipeline is designed as a **reusable, composable module**, not just a script.

```text
Media File
   ↓
[Normalization] → ffmpeg
   ↓
[Chunking] → moviepy
   ↓
[Transcription] → OpenAI
   ↓
[Merging]
   ↓
Transcript (.txt)
````

This modular design allows the transcription layer to plug into:

* Case extraction agents
* Retrieval (RAG) systems
* Clinical reasoning pipelines
* API services (FastAPI)
* Frontend applications

---

## 📦 Supported Inputs

* Video: `.mp4`, `.mov`, `.avi`, `.mkv`
* Audio: `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`

---

## ⚙️ Requirements

* Python **3.12+**
* `ffmpeg` installed and available on `PATH`
* OpenAI API key

---

## 🔧 Installation

Clone the repository and install dependencies:

```powershell
pip install -r requirements.txt
```

Activate virtual environment (recommended):

```powershell
.\.venv\Scripts\Activate.ps1
```

Set your OpenAI API key:

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

---

## ▶️ Usage

Run the pipeline from the project root:

```powershell
python main.py --input "Zeno Minutes.mp4"
```

Or with an absolute path:

```powershell
python main.py --input "C:\path\to\file.mp4"
```

---

## 📤 Outputs

All outputs are written to:

```text
data/output/
```

### Generated artifacts

| Artifact                | Description                       |
| ----------------------- | --------------------------------- |
| `<file>_normalized.wav` | Normalized audio (if disk allows) |
| `chunks/`               | Intermediate audio chunks         |
| `<file>_transcript.txt` | Final merged transcript           |

### Example

```text
data/output/Zeno Minutes_transcript.txt
```

---

## ⚠️ Fault Tolerance

The pipeline is designed to **fail gracefully**:

* If normalization fails due to disk constraints:

  * ✅ Falls back to chunking the original media
  * ❌ Does NOT terminate the pipeline

This ensures robustness in constrained environments.

---

## 🧪 Testing

Run all tests:

```powershell
python -m pytest tests -v
```

---

## 🧩 Roadmap

This repository is evolving into a full **AI-powered post-consultation system**.

### Planned pipeline stages

1. ✅ Transcription (current)
2. 🔜 Case extraction (structured clinical data)
3. 🔜 Illness retrieval (RAG)
4. 🔜 Differential diagnosis generation
5. 🔜 Care plan recommendation
6. 🔜 SOAP notes + patient summaries
7. 🔜 API + frontend integration

---

## 🧠 Design Principles

* **Modular** → each step is independently reusable
* **Deterministic outputs** → consistent file structure
* **Typed contracts (Pydantic)** → safe integration across layers
* **Thin orchestration** → logic lives in tools, not pipelines
* **Production-ready** → logging, testing, fault tolerance

---

## 📌 Example Use Cases

* Clinical consultation transcription
* Medical AI assistants
* Meeting transcription pipelines
* Dataset generation for ASR/LLM systems
* RAG-based healthcare applications

---

## 🤝 Contributing

PRs are structured as **small, focused improvements** aligned with pipeline stages.

---

## 📄 License

MIT License (or specify your license here)

---

## 👤 Author

Built by **Tumelo Konaite**
AI Engineer | Machine Learning Engineer | Quantitative Specialist

---
