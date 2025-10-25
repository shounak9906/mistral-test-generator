<!-- # 🧠 LLM-Powered Test Generator  
### *FastAPI + Mistral SDK + CLI + Full Testing Suite*

This project is a **Python + FastAPI application** that integrates with the **Mistral AI SDK** to automatically generate and execute **unit tests** for Python code.  
It also includes a **command-line interface (CLI)**, **offline stub mode** for deterministic testing, a **sandboxed execution environment**, and **extensive test coverage** to demonstrate engineering best practices.

---

## Project Overview

The application provides a **local and API-based system** for automatically generating and running test cases for arbitrary Python functions or classes.  

Using the **Mistral SDK**, it analyzes user-provided code, infers the symbol (function/class name), and produces corresponding `pytest` test files.  

It supports two main usage modes:
1. **Single-file mode** → all tests go into one file (`test_generated.py`)
2. **Per-symbol mode** → separate test files per detected function/class (`test_<symbol>.py`)

The project is built with **FastAPI**, **Pydantic**, **pytest**, and **Mistral SDK** — wrapped in a developer-friendly **Makefile** and **CLI** for instant usability.

---

## Core Features

### AI Test Generation
- Uses the `mistralai` SDK (or stub mode) to generate pytest tests from Python source code.
- Automatically detects the first function/class name (`symbol`) from the provided file.

### FastAPI Backend
- Exposes clean REST endpoints:
  - `GET /health` – Health check with model and run status  
  - `POST /bundle/generate-and-save` – Generates and saves test files  
  - `POST /bundle/generate-run` – Safely executes tests in sandbox (if enabled)
  - `POST /tests/generate.txt` – Returns generated test code as text (no file writes)
- Built with **Pydantic models** for input/output validation.

### Command-Line Interface (CLI)
- Interacts with backend logic directly — no web server needed.
- Commands:
  ```bash
  python cli.py generate under_test.py --spec "Compute x**y"
  python cli.py run --enable

### Flags

 - `--cleanup` → per-symbol mode (cleans older tests)

 - `--spec` → natural-language description of function behavior

 - `--enable` → explicit permission to run tests (safety guard)

### Makefile automation
  ```bash
  make gen                 # Generate tests (single mode)
  make gen-clean           # Generate tests (per-symbol mode)
  make run                 # Run latest generated tests safely
  make api-test            # Run FastAPI backend tests
  make coverage            # Generate coverage report
  make clean               # Remove caches and coverage data


### Sandbox Execution

Generated tests run in a temporary directory to isolate side effects.

Controlled by _run_enabled() — execution allowed only if ENABLE_RUN=1.
 -->


# Project: Mistral SDK App — FastAPI + CLI + Tests

A production‑ready Python template that wraps the **Mistral AI SDK** behind a small **FastAPI** service and a convenient **CLI**, with **pytest**-based test generation and **coverage** reporting. It’s designed to be simple to run locally (macOS/Apple Silicon friendly), easy to extend, and safe to ship.

> This README is self‑contained: follow it from top to bottom to **download**, **set up**, **run**, and **test** the project.

---

## Table of Contents
- [Features](#features)
- [Repository Layout](#repository-layout)
- [Requirements](#requirements)
- [Quickstart (copy–paste)](#quickstart-copy–paste)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the API](#running-the-api)
- [Using the CLI](#using-the-cli)
- [Testing & Coverage](#testing--coverage)
- [Makefile Commands](#makefile-commands)
- [Development Tips](#development-tips)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Features

- **FastAPI server** exposing clean endpoints around the Mistral AI SDK (text generation and, optionally, embeddings).
- **CLI tool** that mirrors the HTTP API for quick local runs and scripting.
- **Automated test generation** (optional) that writes tests into `tests/generated/`.
- **Coverage integration** via `coverage.py` with HTML and terminal reports.
- **Pluggable backends**: easily switch between **non‑embedding** and **embedding** endpoints.
- **Typed codebase** with friendly errors; Apple‑Silicon/macOS development flow supported.
- **Reproducible builds** via `requirements.txt` and a small `Makefile` with common tasks.
- **Toggle cleanup flags** in generation utilities to control whether intermediate files are kept.

> You can start just with HTTP + CLI; embeddings and generators are optional modules you can disable/ignore if not needed.

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
│  ├─ test_unit_*.py      # Handwritten unit tests
│  └─ generated/          # Auto-generated tests land here
└─ README.md              # You are here
```

> If your project evolved, keep these filenames; otherwise adjust the paths in the Makefile commands below.

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

## Quickstart (copy–paste)

```bash
# 1) Clone or download the project
git clone <YOUR_REPO_URL> mistral-sdk-app && cd mistral-sdk-app

# 2) Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4) Configure your API key (shell or .env)
export MISTRAL_API_KEY="sk-...your-key..."

# 5) Run the API (dev)
make run    # or: uvicorn main:app --reload --port 8000

# 6) In another terminal, try the CLI
source .venv/bin/activate
python cli.py prompt "Hello from CLI"

# 7) Run the test suite with coverage
make coverage
# open htmlcov/index.html for the detailed report
```

---

## Installation

1. **Clone** the repository:
   ```bash
   git clone <YOUR_REPO_URL> mistral-sdk-app
   cd mistral-sdk-app
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
| `APP_HOST` | ❌ | `0.0.0.0` | Bind address for uvicorn. |
| `APP_PORT` | ❌ | `8000` | Port for the FastAPI server. |
| `MODEL_NAME` | ❌ | `mistral-small-latest` | Default text generation model. |
| `EMBED_MODEL` | ❌ | `mistral-embed` | Default embeddings model (if embeddings enabled). |
| `GEN_CLEANUP` | ❌ | `true` | If `false`, keep intermediate artifacts for debugging. |

Create a `.env` (optional):
```env
MISTRAL_API_KEY=sk-...
MODEL_NAME=mistral-small-latest
EMBED_MODEL=mistral-embed
GEN_CLEANUP=true
APP_PORT=8000
```

---

## Running the API

Start the server (development, with auto‑reload):
```bash
make run
# equivalent:
uvicorn main:app --reload --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000}
```

### Available Endpoints (default examples)

- `GET /health` — liveness probe.
- `POST /generate` — text generation.
  - Body: `{ "prompt": "Your prompt", "model": "mistral-small-latest", "max_tokens": 256 }`
- `POST /embed` — text embeddings (optional).
  - Body: `{ "texts": ["foo", "bar"], "model": "mistral-embed" }`

**Example curl calls**

```bash
# Health
curl -s http://localhost:8000/health | jq

# Generate text
curl -s -X POST http://localhost:8000/generate   -H "Content-Type: application/json"   -d '{"prompt":"Say hello","max_tokens":64}' | jq

# Embeddings (if enabled)
curl -s -X POST http://localhost:8000/embed   -H "Content-Type: application/json"   -d '{"texts":["A","B"]}' | jq
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

> Tip: add `alias mistral="python $(pwd)/cli.py"` to your shell profile to call `mistral prompt "..."`.

---

## Testing & Coverage

We use **pytest** and **coverage.py**. Generated tests are written to `tests/generated/` so you can inspect and keep them.

Run all tests with coverage:
```bash
make coverage
# or:
coverage run -m pytest -q
coverage report -m
coverage html  # writes htmlcov/index.html
```

Run a subset of tests:
```bash
pytest -k "under_test and not slow" -q
```

Generate new tests (if your project includes a generator):
```bash
make gen
# or whatever command you configured for test generation
```

> If a generated test is flaky, keep it in `tests/generated/` but mark with `@pytest.mark.flaky(reruns=2)` or adjust the seed.

---

## Makefile Commands

Common developer commands (adjust if your Makefile differs):

```Makefile
# ---- Makefile (excerpt) ----
run:               ## Start FastAPI (dev)
    uvicorn main:app --reload --host $${APP_HOST:-0.0.0.0} --port $${APP_PORT:-8000}

test:              ## Run tests (pytest)
    pytest -q

coverage:          ## Test coverage (terminal + HTML)
    coverage run -m pytest -q
    coverage report -m
    coverage html

gen:               ## Generate tests into tests/generated/
    python -m tools.generate_tests --out tests/generated --cleanup $${GEN_CLEANUP:-true}

clean:             ## Remove caches and artifacts
    rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov dist build
```

List help:
```bash
make help  # if you added a help target
```

---

## Development Tips

- **Type hints**: add `pyright` or `mypy` if you want stricter checks.
- **Formatting**: black + ruff are easy wins for style and lint.
- **Seeds**: make deterministic tests by seeding any random generators.
- **API contracts**: define Pydantic models for request/response; version your routes (`/v1/...`) when you add breaking changes.
- **Apple Silicon**: prefer native `arm64` wheels; if a lib fails to build, try `pip install --only-binary :all:` for that package or use Rosetta as a fallback.

---

## Troubleshooting

**`MISTRAL_API_KEY` not set**
- Ensure it’s exported in your shell *before* starting `uvicorn` or running the CLI.
- On macOS, Terminal sessions don’t share env with GUI apps; export in shell profile or use a `.env` loader.

**Linker / duplicate symbol errors (C++ labs)**
- If you also compile C++ in the same workspace, ensure single definition for utility functions (e.g., a global `error()` function should live in **one** `.cpp` or be `static inline` in a header).

**Python version issues**
- Verify `python --version` is ≥ 3.10. On macOS, prefer `python3` from Homebrew.

**Port already in use**
- Change `APP_PORT` or stop the other process: `lsof -nP -iTCP:8000 | grep LISTEN`.

---

## FAQ

**Q: Do I need embeddings?**  
A: No. The app runs fine with pure text generation. Keep `/embed` and `cli embed` only if you need vector features.

**Q: Where do auto‑generated tests go?**  
A: Into `tests/generated/`. Commit the useful ones and delete noisy cases; you can toggle cleanup via `GEN_CLEANUP` env var.

**Q: Can I switch models?**  
A: Yes—use the `MODEL_NAME` env var for defaults and `--model` flags in CLI/API calls per request.

**Q: How do I run on a different port?**  
A: `APP_PORT=9000 make run`.

---
