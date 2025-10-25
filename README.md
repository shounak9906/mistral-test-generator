# 🧠 LLM-Powered Test Generator  
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
