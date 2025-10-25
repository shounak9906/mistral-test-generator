import os, json, re, time, random, ast, subprocess, tempfile, shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from mistralai import Mistral

MistralAPIException = Exception

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
FALLBACK_MODEL = os.getenv("MISTRAL_FALLBACK_MODEL", "mistral-medium-latest")
STUB_MODE = os.getenv("STUB_GEN") == "1"

if not STUB_MODE and not API_KEY:
    raise RuntimeError("Set MISTRAL_API_KEY in .env or env vars (not required when STUB_GEN=1).")

client = Mistral(api_key=API_KEY) if API_KEY else None
app = FastAPI(title="Spec→Test Generator", version="0.2.0")

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def detect_symbol_name(code: str) -> Optional[str]:
    """Return the first top-level function or class name in the code."""
    try:
        tree = ast.parse(code)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                return node.name
            if isinstance(node, ast.ClassDef):
                return node.name
    except Exception:
        pass
    return None

def _parse_json_from_model(raw_content) -> dict:
    # normalize to string
    if isinstance(raw_content, list):
        parts = []
        for c in raw_content:
            if isinstance(c, dict) and "text" in c:
                parts.append(c["text"])
        text = "".join(parts)
    else:
        text = str(raw_content)

    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    text = _clean_to_first_json(text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            raise HTTPException(status_code=502, detail=f"Model did not return valid JSON. Raw: {text[:800]}")
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=502, detail=f"JSON parse failed: {e}. Raw: {text[:800]}")

def _call_with_retries(model, **kwargs):
    delay = 2.0
    for _ in range(6):  
        try:
            return client.chat.complete(model=model, **kwargs)
        except MistralAPIException as e:
            msg = str(e).lower()
            if "429" in msg or "capacity" in msg or "rate limit" in msg:
                time.sleep(delay + random.uniform(0, 1.5))
                delay = min(delay * 2, 30)
                continue
            raise
    raise HTTPException(status_code=502, detail="Upstream capacity/rate limit after retries.")

def _chat(messages):
    try:
        return _call_with_retries(MODEL, messages=messages, temperature=0, max_tokens=1200)
    except HTTPException:
        return _call_with_retries(FALLBACK_MODEL, messages=messages, temperature=0, max_tokens=1200)
    
def _clean_to_first_json(text: str) -> str:
    text = text.lstrip("\ufeff")
    m = re.search(r"\{", text)
    return text[m.start():] if m else text

def _extract_between(text: str, start: str, end: str) -> str:
    s = text.find(start)
    if s == -1:
        raise HTTPException(status_code=502, detail="Start marker not found in model output.")
    s += len(start)
    e = text.find(end, s)
    if e == -1:
        raise HTTPException(status_code=502, detail="End marker not found in model output.")
    return text[s:e].strip()

def _gen_tests_text(symbol: str, spec: str) -> str:
    """
    When STUB_GEN=1, return a tiny deterministic pytest file.
    Otherwise, call the real model through _chat(...) with RAW_* prompts.
    """
    if os.getenv("STUB_GEN") == "1":
        return (
            f"from under_test import {symbol}\n"
            "import pytest\n\n"
            f"@pytest.mark.parametrize('a,b,expected', [(2, 3, 6)])\n"
            f"def test_{symbol}(a, b, expected):\n"
            f"    assert {symbol}(a, b) == expected\n"
        )

    sysmsg = RAW_SYSTEM.format(symbol=symbol)
    usrmsg = RAW_USER.format(symbol=symbol, spec=spec.strip())
    res = _chat([{"role": "system", "content": sysmsg},
                 {"role": "user", "content": usrmsg}])
    content = res.choices[0].message.content
    if isinstance(content, list):
        content = "".join((c.get("text","") if isinstance(c, dict) else str(c)) for c in content)
    text = str(content)
    return _extract_between(text, "<<<PYTEST_START>>>", "<<<PYTEST_END>>>")

def _ensure_import_line(tests_py: str, symbol: str) -> str:
    if "from under_test import " in tests_py:
        return tests_py
    return f"from under_test import {symbol}\n" + tests_py

def _run_enabled() -> bool:
    return os.getenv("ENABLE_RUN") == "1"

def run_bundle_tests(code_path: str = "under_test.py", tests_path: str = None):
    """
    Run pytest safely in a temporary directory, returning (exit_code, output).
    Reuses the same logic as /bundle/generate-run endpoint.
    """
    import subprocess, tempfile, shutil, os
    from pathlib import Path

    if not tests_path:
        gen_dir = Path("tests/generated")
        candidates = sorted(gen_dir.glob("test_*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            raise RuntimeError("No generated test files found.")
        tests_path = str(candidates[0])

    with tempfile.TemporaryDirectory() as td:
        shutil.copy(code_path, os.path.join(td, "under_test.py"))
        os.makedirs(os.path.join(td, "tests"), exist_ok=True)
        shutil.copy(tests_path, os.path.join(td, "tests", os.path.basename(tests_path)))

        Path(os.path.join(td, "tests", "conftest.py")).write_text(
            "import sys, pathlib\nROOT = pathlib.Path(__file__).resolve().parents[1]\n"
            "sys.path.insert(0, str(ROOT))\n",
            encoding="utf-8"
        )

        cmd = ["pytest", "-q", "tests"]
        run = subprocess.run(
            cmd, cwd=td, capture_output=True, text=True, timeout=10,
            env={**os.environ, "PYTHONPATH": td},
        )

    return run.returncode, run.stdout + run.stderr

# -----------------------------------------------------------------------------
# Prompting
# -----------------------------------------------------------------------------
SYSTEM_MSG_TEMPLATE = """
You must output VALID JSON only with keys:
- "tests_b64": base64-encoded UTF-8 contents of a complete pytest module (preferred)
- "tests_py": plain string of the pytest module (optional, provided only if b64 is impossible)
- "rationale": short string

Rules:
- JSON only (no markdown fences).
- Use only pytest and the Python standard library.
- Prefer pytest.mark.parametrize where sensible.
- For floats, use pytest.approx (never exact == for 0.1+0.2).
- Do not mark str+str or list+list as invalid (Python allows those).
- If the spec forbids non-(int|float), include invalid cases expecting TypeError.
- No side-effects or file/network access in tests.
- Import the target with: from under_test import {symbol}
- Assume 'under_test.py' is at repo root; tests run from 'tests/'. 
- Avoid extraneous characters before or after the JSON (no leading quotes, BOMs, or comments).
"""

USER_TEMPLATE = """Target callable name: {symbol}

Write pytest tests for the callable imported as:
from under_test import {symbol}

Human spec:
{spec}

Size preset: {size}
Style hints: {hints}

Constraints:
- Do not modify the target code.
- The file must be directly runnable by pytest as tests/test_generated.py.
"""

RAW_SYSTEM = """
Return ONLY the pytest file content as plain text, between the markers:
<<<PYTEST_START>>>
... (pytest module text)
<<<PYTEST_END>>>

Rules:
- No JSON, no code fences, no commentary outside the markers.
- Use only pytest + Python stdlib.
- Use pytest.mark.parametrize where sensible.
- For floats: use pytest.approx.
- Import target as: from under_test import {symbol}
- Tests must be self-contained and runnable as tests/test_generated.py.
"""

RAW_USER = """Write a pytest module that tests the callable {symbol} imported as:

from under_test import {symbol}

Human spec:
{spec}

Constraints:
- Do not modify the target code.
- Put ONLY the pytest file content between the markers.
<<<PYTEST_START>>>
<<<PYTEST_END>>>"""

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------
class BundleRequest(BaseModel):
    code: str
    spec: str
    size: str = Field("std", pattern="^(mini|std|max)$")
    style_hints: List[str] = []
    module_path: str = "under_test.py"
    symbol: Optional[str] = None
    tests_mode: str = Field("per_symbol", pattern="^(per_symbol|single)$")
    cleanup_old: bool = True 

class BundleResponse(BaseModel):
    code_path: str
    tests_path: str
    symbol: str
    rationale: str

class GenerateTextRequest(BaseModel):
    code: str
    spec: str
    size: str = Field("std", pattern="^(mini|std|max)$")
    style_hints: List[str] = []
    symbol: Optional[str] = None

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True, "model": MODEL, "fallback": FALLBACK_MODEL}

@app.post("/bundle/generate-and-save", response_model=BundleResponse)
def generate_and_save_bundle(req: BundleRequest):
    code_path = Path(req.module_path)
    code_path.parent.mkdir(parents=True, exist_ok=True)
    code_path.write_text(req.code, encoding="utf-8")

    symbol = req.symbol or detect_symbol_name(req.code)
    if not symbol:
        raise HTTPException(status_code=400, detail="Could not detect a top-level function/class name. Provide 'symbol'.")

    tests_py = _gen_tests_text(symbol, req.spec)
    tests_py = _ensure_import_line(tests_py, symbol)

    tests_root = Path("tests")
    gen_dir = tests_root / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)

    if req.tests_mode == "per_symbol":
        tests_path = gen_dir / f"test_{symbol}.py"
        if req.cleanup_old:
            for p in gen_dir.glob("test_*.py"): 
                if p.name != tests_path.name:
                    try:
                        p.unlink()
                    except Exception:
                        pass
    else:
        tests_path = gen_dir / "test_generated.py"

    conftest = tests_root / "conftest.py"
    if not conftest.exists():
        conftest.write_text(
            "import sys, pathlib\n"
            "ROOT = pathlib.Path(__file__).resolve().parents[1]\n"
            "if str(ROOT) not in sys.path:\n"
            "    sys.path.insert(0, str(ROOT))\n",
            encoding="utf-8",
        )

    tests_path.write_text(tests_py, encoding="utf-8")

    return BundleResponse(
        code_path=str(code_path),
        tests_path=str(tests_path),
        symbol=symbol,
        rationale="Generated via raw-text markers; floats use pytest.approx; imports from under_test.py.",
    )

@app.post("/bundle/generate-run")
def generate_and_run(req: BundleRequest):
    if not _run_enabled():
        raise HTTPException(403, "Test execution disabled. Set ENABLE_RUN=1 to enable.")

    resp = generate_and_save_bundle(req)

    with tempfile.TemporaryDirectory() as td:
        shutil.copy(resp.code_path, os.path.join(td, "under_test.py"))
        os.makedirs(os.path.join(td, "tests"), exist_ok=True)
        shutil.copy(resp.tests_path, os.path.join(td, "tests", os.path.basename(resp.tests_path)))

        Path(os.path.join(td, "tests", "conftest.py")).write_text(
            "import sys, pathlib\nROOT = pathlib.Path(__file__).resolve().parents[1]\n"
            "sys.path.insert(0, str(ROOT))\n",
            encoding="utf-8",
        )

        cmd = ["pytest", "-q", "tests"]
        try:
            run = subprocess.run(
                cmd,
                cwd=td,
                capture_output=True,
                text=True,
                timeout=10,  
                env={**os.environ, "PYTHONPATH": td},
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "pytest timed out")

    return {
        "code_path": resp.code_path,
        "tests_path": resp.tests_path,
        "symbol": resp.symbol,
        "exit_code": run.returncode,
        "stdout": run.stdout[-4000:],  
        "stderr": run.stderr[-4000:],
    }

@app.post("/tests/generate.txt", response_class=PlainTextResponse)
def generate_tests_text(req: GenerateTextRequest):
    symbol = req.symbol or detect_symbol_name(req.code) or "target"
    Path("under_test.py").write_text(req.code, encoding="utf-8")

    tests_py = _gen_tests_text(symbol, req.spec)

    tests_py = _ensure_import_line(tests_py, symbol)
    
    return tests_py

"""
curl -sS -X POST http://127.0.0.1:8000/bundle/generate-run \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "code": "def pow(a,b):\n    return a ** b\n",
  "spec": "Only ints/floats allowed; all other types must raise TypeError. Use pytest.approx for float products.",
  "module_path": "under_test.py",
  "tests_mode": "per_symbol",
  "cleanup_old": true
}
JSON
"""
#Only ints/floats allowed and booleans allowed as ints, don't test strings or chars; all other types must raise TypeError. Use pytest.approx for float products.
"""
curl -sS -X POST http://127.0.0.1:8000/bundle/generate-run \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "code": "def mult(a,b):\n    return a * b\n",
  "spec": "Only test for ints/floats, don't test any other datatype. Use pytest.approx for float products.",
  "module_path": "under_test.py",
  "tests_mode": "per_symbol",
  "cleanup_old": true
}
JSON
"""

"""
coverage run -m pytest -q && coverage report -m
"""