# Project: Mistral SDK App — FastAPI + CLI + Tests

A production‑ready Python template that wraps the **Mistral AI SDK** behind a small **FastAPI** service and a convenient **CLI**, with **pytest**-based test generation and **coverage** reporting. It’s designed to be simple to run locally, easy to extend, and safe to ship.

> This README is self‑contained: follow it from top to bottom to **download**, **set up**, **run**, and **test** the project.

---

## Table of Contents
- [Features](#features)
- [Repository Layout](#repository-layout)
- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the API](#running-the-api)
- [Using the CLI](#using-the-cli)
- [Testing & Coverage](#testing--coverage)
- [Makefile Commands](#makefile-commands)
- [Troubleshooting](#troubleshooting)
---

## Features

- **FastAPI server** exposing clean endpoints around the Mistral AI SDK (text generation and, optionally, embeddings).
- **CLI tool** that mirrors the HTTP API for quick local runs and scripting.
- **Automated test generation** (optional) that writes tests into `tests/generated/`.
- **Coverage integration** via `coverage.py` with HTML and terminal reports.
- **Reproducible builds** via `requirements.txt` and a small `Makefile` with common tasks.
- **Toggle cleanup flags** in generation utilities to control whether intermediate files are kept.

---

## Repository Layout

```
.
├─ main.py                # FastAPI app entrypoint (exposes routes)
├─ cli.py                 # Click/Typer-based CLI (mirrors API features)
├─ under_test.py          # Small module with functions covered by tests
├─ requirements.txt       # Python dependencies
├─ Makefile               # Developer commands (run, test, coverage, gen, clean)
├─ tests/
│  ├─ test_api.py         # Integration tests for the FastAPI endpoints (/health, /generate, /embed)
│  └─ generated/          # Auto-generated tests land here
└─ README.md              # You are here
```

---

## Requirements

- **Python** ≥ 3.10 (3.11 recommended)
- **pip** ≥ 22 and **virtualenv** or **conda** (any venv manager is fine)
- macOS (Apple Silicon **arm64** supported) or Linux
- A **Mistral API key** (environment variable: `MISTRAL_API_KEY`)

Optional but recommended:
- **Make** (preinstalled on macOS Xcode CLT)
- **pytest**, **coverage** (installed via `requirements.txt`)

---

## Quickstart

```bash
# 1) Clone or download the project
git clone https://github.com/shounak9906/mistral-test-generator mistral-sdk-app && cd mistral-sdk-app

# 2) Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4) Configure your API key (shell or .env)
export MISTRAL_API_KEY="sk-...your-key..."

# 5) Run the API (dev)
uvicorn main:app --reload --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000}

# 6) Run the test suite with coverage
make coverage
# open htmlcov/index.html for the detailed report
```

---

## Installation

1. **Clone** the repository:
   ```bash
   git clone https://github.com/shounak9906/mistral-test-generator.git
   cd mistral-test-generator
   ```

2. **Create a virtual environment** (macOS/Linux):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   *(Windows PowerShell)*
   ```powershell
   py -3 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## Configuration

The application reads configuration from **environment variables** (or a `.env` file if you use `python-dotenv`). The key settings are:

| Variable | Required | Default | Description |
|---|---|---|---|
| `MISTRAL_API_KEY` | ✅ | — | Your Mistral API key used by the SDK. |
| `MODEL_NAME` | ❌ | `mistral-small-latest` | Default text generation model. |
| `EMBED_MODEL` | ❌ | `mistral-embed` | Default embeddings model (if embeddings enabled). |
| `GEN_CLEANUP` | ❌ | `true` | If `false`, keep intermediate artifacts for debugging. |

Create a `.env` (optional):
```env
MISTRAL_API_KEY=sk-...
MODEL_NAME=mistral-small-latest
EMBED_MODEL=mistral-embed
GEN_CLEANUP=true
```

---

## Running the API

Start the server:
```bash
uvicorn main:app --reload --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000}
```

### Available Endpoints (project-specific)

- `GET /health` — liveness & model info.  
  Returns: `{"ok": true, "model": "<MISTRAL_MODEL>", "fallback": "<MISTRAL_FALLBACK_MODEL>"}`

- `POST /bundle/generate-and-save` — generate pytest tests **and save** to disk.  
  Body (`BundleRequest`): `{"code": str, "spec": str, "size": "mini|std|max", "style_hints": [str], "module_path": "under_test.py", "symbol": str|null, "tests_mode": "per_symbol|single", "cleanup_old": true}`  
  Returns (`BundleResponse`): `{"code_path": str, "tests_path": str, "symbol": str, "rationale": str}`

- `POST /bundle/generate-and-run` — generate tests **and run** them (returns pytest output).  
  Body: same as `BundleRequest`  
  Returns: `{"exit_code": int, "stdout": str, "stderr": str}`

- `POST /tests/generate.txt` — return the generated pytest file as **plain text**.  
  Body (`GenerateTextRequest`): `{"code": str, "spec": str, "size": "mini|std|max", "style_hints": [str], "symbol": str|null}`


**Example curl calls**

- `POST /bundle/generate-and-save` — generate pytest tests **and save them to disk**.  
  **Body** (`BundleRequest`):
  
  ```json
  {
    "code": "str",
    "spec": "str",
    "size": "mini|std|max",
    "style_hints": ["str", "..."],
    "module_path": "under_test.py",
    "symbol": "str or null",
    "tests_mode": "per_symbol|single",
    "cleanup_old": true
  }
  ```


- Returns (`BundleResponse`):
    ```json
    {
      "code_path": "str",
      "tests_path": "str",
      "symbol": "str",
      "rationale": "str"
    }
    ```


---

## Using the CLI

The CLI mirrors the API and is handy for local testing or shell scripts.

```bash
# Basic prompt (uses MODEL_NAME unless overridden)
python cli.py prompt "Explain Chernoff bounds in one line"

# Choose a model and max tokens
python cli.py prompt "Summarize Weierstrass theorem" --model mistral-small-latest --max-tokens 128

# Embeddings (if implemented)
python cli.py embed "first sentence" "second sentence" --model mistral-embed

# Batch from a file (one prompt per line)
python cli.py batch prompts.txt --out outputs.txt
```

---

## Testing & Coverage

### API Integration Tests (`tests/test_api.py`)

This suite exercises the **running FastAPI server** (or the app via `TestClient`) and covers endpoints like:
- `GET /health`
- `POST /generate`
- `POST /embed` (if enabled)

**Run just the API tests**:
```bash
pytest -q tests/test_api.py
```

We use **pytest** and **coverage.py**. Generated tests are written to `tests/generated/` so you can inspect and keep them.

Run all tests with coverage:
```bash
make coverage
```

Run all tests:
```bash
make test
```

Run all tests with coverage:
```bash
make coverage
```

API integration tests only:
```bash
make api-test
```

Generate tests with the CLI:
```bash
# Single test file (optionally pass a spec):
make gen                

# Per-symbol output with cleanup:
make gen-clean          
```

Run the latest test file
```bash
make run                
```

---

## Troubleshooting

**`MISTRAL_API_KEY` not set**
- Ensure it’s exported in your shell *before* starting `uvicorn` or running the CLI.

**Python version issues**
- Verify `python --version` is ≥ 3.10. On macOS, prefer `python3` from Homebrew.

---
