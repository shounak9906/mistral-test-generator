import importlib
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client_stub(monkeypatch):
    """
    Client in STUB mode (no external API key needed).
    Does NOT enable running tests via /bundle/generate-and-run.
    """
    monkeypatch.setenv("STUB_GEN", "1")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    import main  
    importlib.reload(main)
    return TestClient(main.app)


@pytest.fixture
def client_with_run(monkeypatch):
    """
    Client in STUB mode with 'run' explicitly enabled.
    """
    monkeypatch.setenv("STUB_GEN", "1")
    monkeypatch.setenv("ENABLE_RUN", "1")
    monkeypatch.setenv("RUN_ENABLED", "1") 

    import main  
    importlib.reload(main)
    return TestClient(main.app)


# ---------- Tests ----------

def test_health(client_stub):
    r = client_stub.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert "model" in body and "fallback" in body


def test_bundle_generate_and_save_ok(client_stub, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    payload = {
        "code": "def power(a,b):\n    return a ** b\n",
        "spec": "Only test for ints/floats. For floats use pytest.approx.",
        "size": "std",
        "style_hints": [],
        "module_path": "under_test.py",
        "symbol": "power",
        "tests_mode": "per_symbol",
        "cleanup_old": True,
    }
    r = client_stub.post("/bundle/generate-and-save", json=payload)
    assert r.status_code == 200
    data = r.json()
    for k in ("code_path", "tests_path", "symbol", "rationale"):
        assert k in data
    assert (tmp_path / data["code_path"]).exists()
    assert (tmp_path / data["tests_path"]).exists()


def test_bundle_generate_run_disabled(client_stub, monkeypatch, tmp_path):
    """
    Without ENABLE_RUN, /bundle/generate-and-run should reject (403).
    """
    monkeypatch.chdir(tmp_path)
    payload = {
        "code": "def x():\n    return None\n",
        "spec": "n/a",
        "module_path": "under_test.py",
    }
    r = client_stub.post("/bundle/generate-and-run", json=payload)
    assert r.status_code == 403


def test_bundle_generate_and_run_ok(client_with_run, monkeypatch, tmp_path):
    """
    With run enabled, it should execute pytest and return exit_code/stdout/stderr.
    """
    monkeypatch.chdir(tmp_path)
    payload = {
        "code": "def power(a,b):\n    return a ** b\n",
        "spec": "Only ints/floats; pytest.approx for floats.",
        "module_path": "under_test.py",
        "tests_mode": "per_symbol",
        "cleanup_old": True,
    }
    r = client_with_run.post("/bundle/generate-and-run", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("exit_code"), int)
    assert "stdout" in data and "stderr" in data


def test_generate_tests_plain_text(client_stub, monkeypatch, tmp_path):
    """
    /tests/generate.txt returns text/plain with raw pytest source.
    """
    monkeypatch.chdir(tmp_path)
    payload = {
        "code": "def power(a,b):\n    return a ** b\n",
        "spec": "Only ints/floats; pytest.approx for floats.",
        "size": "std",
        "style_hints": [],
        "symbol": "power",
    }
    r = client_stub.post("/tests/generate.txt", json=payload, headers={"Accept": "text/plain"})
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/plain")
    body = r.text
    assert "def test" in body or "pytest" in body.lower()
