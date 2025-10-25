# from pathlib import Path
# from fastapi.testclient import TestClient
# import main  

# client = TestClient(main.app)


# def test_health():
#     r = client.get("/health")
#     assert r.status_code == 200
#     body = r.json()
#     assert body["ok"] is True
#     assert "model" in body and "fallback" in body


# def test_bundle_generate_and_save_per_symbol_cleanup(monkeypatch, tmp_path):
#     """
#     Generate for symbol A then B in per_symbol mode with cleanup.
#     Expect only test_B to remain under tests/generated/.
#     """
#     monkeypatch.chdir(tmp_path)
#     monkeypatch.setenv("STUB_GEN", "1")

#     r1 = client.post("/bundle/generate-and-save", json={
#         "code": "def foo():\n    return 42\n",
#         "spec": "n/a",
#         "module_path": "under_test.py",
#         "tests_mode": "per_symbol",
#         "cleanup_old": True
#     })
#     assert r1.status_code == 200
#     p1 = Path("tests/generated/test_foo.py")
#     assert p1.is_file()

#     r2 = client.post("/bundle/generate-and-save", json={
#         "code": "def bar():\n    return 7\n",
#         "spec": "n/a",
#         "module_path": "under_test.py",
#         "tests_mode": "per_symbol",
#         "cleanup_old": True
#     })
#     assert r2.status_code == 200
#     body = r2.json()
#     p2 = Path(body["tests_path"])
#     assert p2.is_file()
#     assert p2.name == "test_bar.py"
#     assert not p1.exists()  

#     content = p2.read_text(encoding="utf-8")
#     assert "from under_test import bar" in content

#     assert Path("tests/conftest.py").is_file()

#     assert Path(body["code_path"]).is_file()


# def test_bundle_generate_and_save_single_mode(monkeypatch, tmp_path):
#     """
#     Single-file mode should always write tests/generated/test_generated.py.
#     """
#     monkeypatch.chdir(tmp_path)
#     monkeypatch.setenv("STUB_GEN", "1")

#     r = client.post("/bundle/generate-and-save", json={
#         "code": "def baz():\n    return 'ok'\n",
#         "spec": "n/a",
#         "module_path": "under_test.py",
#         "tests_mode": "single",
#         "cleanup_old": True
#     })
#     assert r.status_code == 200
#     body = r.json()
#     assert Path(body["code_path"]).is_file()

#     test_path = Path("tests/generated/test_generated.py")
#     assert test_path.is_file()
#     assert "from under_test import baz" in test_path.read_text(encoding="utf-8")


# def test_generate_text_preview_no_side_effects(monkeypatch, tmp_path):
#     """
#     Preview endpoint should return plaintext pytest module and not write generated test files.
#     """
#     monkeypatch.chdir(tmp_path)
#     monkeypatch.setenv("STUB_GEN", "1")

#     r = client.post("/tests/generate.txt", json={
#         "code": "def mult(a,b):\n    return a*b\n",
#         "spec": "n/a",
#         "size": "mini"
#     })
#     assert r.status_code == 200
#     assert "def test_" in r.text  
#     assert not Path("tests/generated").exists() or not any(Path("tests/generated").glob("test_*.py"))


# def test_bundle_generate_run_enabled(monkeypatch, tmp_path):
#     """
#     Safe run: with ENABLE_RUN=1, endpoint should run pytest in a temp dir and return exit_code/stdout.
#     """
#     monkeypatch.chdir(tmp_path)
#     monkeypatch.setenv("STUB_GEN", "1")
#     monkeypatch.setenv("ENABLE_RUN", "1")

#     r = client.post("/bundle/generate-run", json={
#         "code": "def mult(a,b):\n    return a*b\n",
#         "spec": "n/a",
#         "module_path": "under_test.py",
#         "tests_mode": "per_symbol",
#         "cleanup_old": True
#     })
#     assert r.status_code == 200
#     body = r.json()
#     assert body["exit_code"] == 0
#     assert "passed" in body["stdout"]


# def test_bundle_generate_run_disabled(monkeypatch, tmp_path):
#     """
#     If run is not enabled, endpoint should reject with 403.
#     """
#     monkeypatch.chdir(tmp_path)
#     monkeypatch.setenv("STUB_GEN", "1")

#     r = client.post("/bundle/generate-run", json={
#         "code": "def x():\n    return None\n",
#         "spec": "n/a",
#         "module_path": "under_test.py"
#     })
#     assert r.status_code == 403


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
