import os
import subprocess
import sys
from pathlib import Path


def test_smoke_test_script_exists():
    assert Path("scripts/smoke_test_llm.py").exists()


def test_smoke_test_without_api_key_has_clear_message():
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = ""
    result = subprocess.run(
        [sys.executable, "scripts/smoke_test_llm.py"],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "cp .env.example .env" in output
    assert "edit .env" in output


def test_smoke_test_script_does_not_print_api_key():
    text = Path("scripts/smoke_test_llm.py").read_text(encoding="utf-8")

    assert "api_key" not in text
