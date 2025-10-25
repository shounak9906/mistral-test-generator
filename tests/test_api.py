from pathlib import Path
from fastapi.testclient import TestClient
import main  

client = TestClient(main.app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "model" in body and "fallback" in body


def test_bundle_generate_and_save_per_symbol_cleanup(monkeypatch, tmp_path):
    """
    Generate for symbol A then B in per_symbol mode with cleanup.
    Expect only test_B to remain under tests/generated/.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STUB_GEN", "1")

    # First symbol
    r1 = client.post("/bundle/generate-and-save", json={
        "code": "def foo():\n    return 42\n",
        "spec": "n/a",
        "module_path": "under_test.py",
        "tests_mode": "per_symbol",
        "cleanup_old": True
    })
    assert r1.status_code == 200
    p1 = Path("tests/generated/test_foo.py")
    assert p1.is_file()

    # Second symbol (should remove prior generated tests)
    r2 = client.post("/bundle/generate-and-save", json={
        "code": "def bar():\n    return 7\n",
        "spec": "n/a",
        "module_path": "under_test.py",
        "tests_mode": "per_symbol",
        "cleanup_old": True
    })
    assert r2.status_code == 200
    body = r2.json()
    p2 = Path(body["tests_path"])
    assert p2.is_file()
    assert p2.name == "test_bar.py"
    assert not p1.exists()  # cleaned up

    # Import line present
    content = p2.read_text(encoding="utf-8")
    assert "from under_test import bar" in content

    # conftest lives at tests/
    assert Path("tests/conftest.py").is_file()

    # Code file written at requested module_path
    assert Path(body["code_path"]).is_file()


def test_bundle_generate_and_save_single_mode(monkeypatch, tmp_path):
    """
    Single-file mode should always write tests/generated/test_generated.py.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STUB_GEN", "1")

    r = client.post("/bundle/generate-and-save", json={
        "code": "def baz():\n    return 'ok'\n",
        "spec": "n/a",
        "module_path": "under_test.py",
        "tests_mode": "single",
        "cleanup_old": True
    })
    assert r.status_code == 200
    body = r.json()
    assert Path(body["code_path"]).is_file()

    test_path = Path("tests/generated/test_generated.py")
    assert test_path.is_file()
    assert "from under_test import baz" in test_path.read_text(encoding="utf-8")


def test_generate_text_preview_no_side_effects(monkeypatch, tmp_path):
    """
    Preview endpoint should return plaintext pytest module and not write generated test files.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STUB_GEN", "1")

    r = client.post("/tests/generate.txt", json={
        "code": "def mult(a,b):\n    return a*b\n",
        "spec": "n/a",
        "size": "mini"
    })
    assert r.status_code == 200
    assert "def test_" in r.text  # got a pytest test back
    # No generated test file unless your preview endpoint intentionally writes one
    assert not Path("tests/generated").exists() or not any(Path("tests/generated").glob("test_*.py"))


def test_bundle_generate_run_enabled(monkeypatch, tmp_path):
    """
    Safe run: with ENABLE_RUN=1, endpoint should run pytest in a temp dir and return exit_code/stdout.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STUB_GEN", "1")
    monkeypatch.setenv("ENABLE_RUN", "1")

    r = client.post("/bundle/generate-run", json={
        "code": "def mult(a,b):\n    return a*b\n",
        "spec": "n/a",
        "module_path": "under_test.py",
        "tests_mode": "per_symbol",
        "cleanup_old": True
    })
    assert r.status_code == 200
    body = r.json()
    assert body["exit_code"] == 0
    assert "passed" in body["stdout"]


def test_bundle_generate_run_disabled(monkeypatch, tmp_path):
    """
    If run is not enabled, endpoint should reject with 403.
    """
    monkeypatch.chdir(tmp_path)
    # Do NOT set ENABLE_RUN
    monkeypatch.setenv("STUB_GEN", "1")

    r = client.post("/bundle/generate-run", json={
        "code": "def x():\n    return None\n",
        "spec": "n/a",
        "module_path": "under_test.py"
    })
    assert r.status_code == 403
