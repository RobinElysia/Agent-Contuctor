"""Concrete local sandbox adapter implementations."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from agentconductor.domain.execution import (
    CodeCandidate,
    SandboxExecutionResult,
    SandboxTestSpec,
    TestingOutcome,
)
from agentconductor.domain.models import ProblemInstance


class PythonSubprocessSandboxAdapter:
    """Evaluate Python candidates in a short-lived local subprocess."""

    def __init__(self, *, timeout_seconds: float = 1.0) -> None:
        self._timeout_seconds = timeout_seconds

    def evaluate(
        self,
        problem: ProblemInstance,
        candidate: CodeCandidate,
        spec: SandboxTestSpec,
    ) -> SandboxExecutionResult:
        del problem
        if candidate.language != "python":
            return SandboxExecutionResult(
                outcome=TestingOutcome.COMPILATION_ERROR,
                diagnostics=(f"Unsupported candidate language '{candidate.language}'.",),
            )

        with tempfile.TemporaryDirectory(prefix="agentconductor-sbx-") as temp_dir:
            sandbox_root = Path(temp_dir)
            candidate_path = sandbox_root / "candidate.py"
            result_path = sandbox_root / "result.json"
            harness_path = sandbox_root / "harness.py"

            candidate_path.write_text(candidate.source_code, encoding="utf-8")
            harness_path.write_text(
                _build_harness(spec=spec, result_path=result_path.name),
                encoding="utf-8",
            )

            try:
                completed = subprocess.run(
                    [sys.executable, harness_path.name],
                    cwd=sandbox_root,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return SandboxExecutionResult(
                    outcome=TestingOutcome.TIME_LIMIT_EXCEEDED,
                    diagnostics=(
                        f"Sandbox execution exceeded {self._timeout_seconds:.1f}s timeout.",
                    ),
                )

            if not result_path.exists():
                stderr = completed.stderr.strip()
                diagnostics = (
                    "Sandbox harness did not produce a structured result.",
                )
                if stderr:
                    diagnostics = diagnostics + (stderr,)
                return SandboxExecutionResult(
                    outcome=TestingOutcome.RUNTIME_ERROR,
                    diagnostics=diagnostics,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    exit_code=completed.returncode,
                )

            payload = json.loads(result_path.read_text(encoding="utf-8"))
            return SandboxExecutionResult(
                outcome=TestingOutcome(payload["outcome"]),
                diagnostics=tuple(payload.get("diagnostics", ())),
                stdout=payload.get("stdout", completed.stdout),
                stderr=payload.get("stderr", completed.stderr),
                exit_code=completed.returncode,
            )


def _build_harness(*, spec: SandboxTestSpec, result_path: str) -> str:
    required_substrings = ", ".join(repr(value.lower()) for value in spec.required_substrings)
    return f"""import importlib.util
import json
from pathlib import Path

RESULT_PATH = Path({result_path!r})
ENTRYPOINT = {spec.entrypoint!r}
REQUIRED_SUBSTRINGS = [{required_substrings}]


def write_result(payload):
    RESULT_PATH.write_text(json.dumps(payload), encoding="utf-8")


try:
    spec = importlib.util.spec_from_file_location("candidate", "candidate.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
except SyntaxError as exc:
    write_result({{
        "outcome": "compilation_error",
        "diagnostics": [f"Compilation failed: {{exc.msg}} at line {{exc.lineno}}."],
    }})
    raise SystemExit(0)
except Exception as exc:
    write_result({{
        "outcome": "runtime_error",
        "diagnostics": [f"Module import failed: {{exc.__class__.__name__}}: {{exc}}."],
    }})
    raise SystemExit(0)

entrypoint = getattr(module, ENTRYPOINT, None)
if entrypoint is None or not callable(entrypoint):
    write_result({{
        "outcome": "runtime_error",
        "diagnostics": [f"Required callable '{{ENTRYPOINT}}' was not defined."],
    }})
    raise SystemExit(0)

try:
    value = entrypoint()
except MemoryError:
    write_result({{
        "outcome": "memory_limit_exceeded",
        "diagnostics": ["Candidate raised MemoryError during execution."],
    }})
    raise SystemExit(0)
except Exception as exc:
    write_result({{
        "outcome": "runtime_error",
        "diagnostics": [f"Candidate raised {{exc.__class__.__name__}}: {{exc}}."],
    }})
    raise SystemExit(0)

if not isinstance(value, str):
    write_result({{
        "outcome": "wrong_answer",
        "diagnostics": ["solve() must return a string for the local sandbox harness."],
        "stdout": repr(value),
    }})
    raise SystemExit(0)

normalized_value = value.lower()
missing = [token for token in REQUIRED_SUBSTRINGS if token not in normalized_value]
if missing:
    write_result({{
        "outcome": "wrong_answer",
        "diagnostics": [f"Returned value missed required token(s): {{', '.join(missing)}}."],
        "stdout": value,
    }})
    raise SystemExit(0)

write_result({{
    "outcome": "passed",
    "diagnostics": ["Local sandbox accepted the candidate code."],
    "stdout": value,
}})
raise SystemExit(0)
"""
