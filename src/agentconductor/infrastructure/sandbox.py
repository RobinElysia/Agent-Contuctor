"""Concrete local judge adapter implementations."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from agentconductor.domain.execution import (
    CodeCandidate,
    JudgeCaseResult,
    JudgeTestCase,
    SandboxExecutionResult,
    SandboxTestSpec,
    TestingOutcome,
)
from agentconductor.domain.models import ProblemInstance


class PythonSubprocessJudgeAdapter:
    """Evaluate Python candidates in a short-lived local subprocess judge."""

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

        timeout_seconds = max(
            spec.resource_limits.cpu_time_seconds,
            self._timeout_seconds,
        )
        with tempfile.TemporaryDirectory(prefix="agentconductor-judge-") as temp_dir:
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
                    timeout=timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return SandboxExecutionResult(
                    outcome=TestingOutcome.TIME_LIMIT_EXCEEDED,
                    diagnostics=(
                        f"Judge execution exceeded {timeout_seconds:.1f}s timeout.",
                    ),
                )

            if not result_path.exists():
                stderr = completed.stderr.strip()
                diagnostics = ("Judge harness did not produce a structured result.",)
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
                case_results=tuple(
                    JudgeCaseResult(
                        name=case_payload["name"],
                        outcome=TestingOutcome(case_payload["outcome"]),
                        diagnostics=tuple(case_payload.get("diagnostics", ())),
                        actual_output=case_payload.get("actual_output"),
                        expected_output=case_payload.get("expected_output"),
                        actual_stdout=case_payload.get("actual_stdout"),
                        expected_stdout=case_payload.get("expected_stdout"),
                    )
                    for case_payload in payload.get("case_results", ())
                ),
                stdout=payload.get("stdout", completed.stdout),
                stderr=payload.get("stderr", completed.stderr),
                exit_code=completed.returncode,
            )


PythonSubprocessSandboxAdapter = PythonSubprocessJudgeAdapter


def _build_harness(*, spec: SandboxTestSpec, result_path: str) -> str:
    payload = {
        "entrypoint": spec.entrypoint,
        "test_cases": [_serialize_test_case(test_case) for test_case in spec.test_cases],
        "resource_limits": {
            "cpu_time_seconds": spec.resource_limits.cpu_time_seconds,
            "memory_limit_bytes": spec.resource_limits.memory_limit_bytes,
        },
    }
    payload_json = json.dumps(payload)
    return f"""import contextlib
import importlib.util
import io
import json
import sys
import tracemalloc
from pathlib import Path

RESULT_PATH = Path({result_path!r})
SPEC = json.loads({payload_json!r})
ENTRYPOINT = SPEC["entrypoint"]
TEST_CASES = SPEC["test_cases"]
RESOURCE_LIMITS = SPEC["resource_limits"]


def write_result(payload):
    RESULT_PATH.write_text(json.dumps(payload), encoding="utf-8")


def normalize(value):
    if isinstance(value, str):
        value = value.replace("\\r\\n", "\\n").replace("\\r", "\\n")
        lines = value.split("\\n")
        normalized_lines = [line.rstrip(" \\t") for line in lines]
        while normalized_lines and normalized_lines[-1] == "":
            normalized_lines.pop()
        return "\\n".join(normalized_lines)
    return value


case_results = []


try:
    spec = importlib.util.spec_from_file_location("candidate", "candidate.py")
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
except SyntaxError as exc:
    write_result({{
        "outcome": "compilation_error",
        "diagnostics": [f"Compilation failed: {{exc.msg}} at line {{exc.lineno}}."],
        "case_results": case_results,
    }})
    raise SystemExit(0)
except Exception as exc:
    write_result({{
        "outcome": "runtime_error",
        "diagnostics": [f"Module import failed: {{exc.__class__.__name__}}: {{exc}}."],
        "case_results": case_results,
    }})
    raise SystemExit(0)

entrypoint = getattr(module, ENTRYPOINT, None)
if entrypoint is None or not callable(entrypoint):
    write_result({{
        "outcome": "runtime_error",
        "diagnostics": [f"Required callable '{{ENTRYPOINT}}' was not defined."],
        "case_results": case_results,
    }})
    raise SystemExit(0)

if not TEST_CASES:
    write_result({{
        "outcome": "runtime_error",
        "diagnostics": ["Judge spec must contain at least one test case."],
        "case_results": case_results,
    }})
    raise SystemExit(0)

for case in TEST_CASES:
    original_stdin = sys.stdin
    stdout_buffer = io.StringIO()
    captured_stdout = ""
    value = None
    try:
        if case.get("stdin_text") is not None:
            sys.stdin = io.StringIO(case["stdin_text"])
        tracemalloc.start()
        with contextlib.redirect_stdout(stdout_buffer):
            value = entrypoint(
                *case.get("arguments", []),
                **case.get("keyword_arguments", {{}}),
            )
        _, peak_bytes = tracemalloc.get_traced_memory()
        captured_stdout = stdout_buffer.getvalue()
    except MemoryError:
        case_results.append({{
            "name": case["name"],
            "outcome": "memory_limit_exceeded",
            "diagnostics": [f"Candidate exhausted memory during case '{{case['name']}}'."],
        }})
        write_result({{
            "outcome": "memory_limit_exceeded",
            "diagnostics": [f"Candidate exhausted memory during case '{{case['name']}}'."],
            "case_results": case_results,
        }})
        raise SystemExit(0)
    except Exception as exc:
        case_results.append({{
            "name": case["name"],
            "outcome": "runtime_error",
            "diagnostics": [
                f"Candidate raised {{exc.__class__.__name__}} during case '{{case['name']}}': {{exc}}."
            ],
            "actual_stdout": stdout_buffer.getvalue(),
        }})
        write_result({{
            "outcome": "runtime_error",
            "diagnostics": [
                f"Candidate raised {{exc.__class__.__name__}} during case '{{case['name']}}': {{exc}}."
            ],
            "case_results": case_results,
            "stdout": stdout_buffer.getvalue(),
        }})
        raise SystemExit(0)
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        sys.stdin = original_stdin

    memory_limit = RESOURCE_LIMITS.get("memory_limit_bytes")
    if memory_limit is not None and peak_bytes > memory_limit:
        case_results.append({{
            "name": case["name"],
            "outcome": "memory_limit_exceeded",
            "diagnostics": [
                f"Case '{{case['name']}}' exceeded the soft memory limit: "
                f"{{peak_bytes}} > {{memory_limit}} bytes."
            ],
            "actual_output": value,
            "actual_stdout": captured_stdout,
        }})
        write_result({{
            "outcome": "memory_limit_exceeded",
            "diagnostics": [
                f"Case '{{case['name']}}' exceeded the soft memory limit: "
                f"{{peak_bytes}} > {{memory_limit}} bytes."
            ],
            "case_results": case_results,
            "stdout": captured_stdout,
        }})
        raise SystemExit(0)

    expected_output = case.get("expected_output")
    if expected_output is not None and normalize(value) != normalize(expected_output):
        case_results.append({{
            "name": case["name"],
            "outcome": "wrong_answer",
            "diagnostics": [
                f"Case '{{case['name']}}' returned {{value!r}}; expected {{expected_output!r}}."
            ],
            "actual_output": value,
            "expected_output": expected_output,
            "actual_stdout": captured_stdout,
            "expected_stdout": case.get("expected_stdout"),
        }})
        write_result({{
            "outcome": "wrong_answer",
            "diagnostics": [
                f"Case '{{case['name']}}' returned {{value!r}}; expected {{expected_output!r}}."
            ],
            "case_results": case_results,
            "stdout": captured_stdout,
        }})
        raise SystemExit(0)

    expected_stdout = case.get("expected_stdout")
    if expected_stdout is not None and normalize(captured_stdout) != normalize(expected_stdout):
        case_results.append({{
            "name": case["name"],
            "outcome": "wrong_answer",
            "diagnostics": [
                f"Case '{{case['name']}}' printed {{captured_stdout.strip()!r}}; "
                f"expected {{expected_stdout!r}}."
            ],
            "actual_output": value,
            "expected_output": expected_output,
            "actual_stdout": captured_stdout,
            "expected_stdout": expected_stdout,
        }})
        write_result({{
            "outcome": "wrong_answer",
            "diagnostics": [
                f"Case '{{case['name']}}' printed {{captured_stdout.strip()!r}}; "
                f"expected {{expected_stdout!r}}."
            ],
            "case_results": case_results,
            "stdout": captured_stdout,
        }})
        raise SystemExit(0)

    case_results.append({{
        "name": case["name"],
        "outcome": "passed",
        "actual_output": value,
        "expected_output": expected_output,
        "actual_stdout": captured_stdout,
        "expected_stdout": expected_stdout,
    }})

write_result({{
    "outcome": "passed",
    "diagnostics": [f"Judge accepted the candidate across {{len(TEST_CASES)}} case(s)."],
    "case_results": case_results,
    "stdout": "",
}})
raise SystemExit(0)
"""


def _serialize_test_case(test_case: JudgeTestCase) -> dict[str, object]:
    return {
        "name": test_case.name,
        "arguments": list(test_case.arguments),
        "keyword_arguments": dict(test_case.keyword_arguments),
        "stdin_text": test_case.stdin_text,
        "expected_output": test_case.expected_output,
        "expected_stdout": test_case.expected_stdout,
    }
