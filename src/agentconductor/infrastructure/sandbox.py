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
        if not spec.test_cases:
            return SandboxExecutionResult(
                outcome=TestingOutcome.RUNTIME_ERROR,
                diagnostics=("Judge spec must contain at least one test case.",),
            )

        with tempfile.TemporaryDirectory(prefix="agentconductor-judge-") as temp_dir:
            sandbox_root = Path(temp_dir)
            candidate_path = sandbox_root / "candidate.py"
            harness_path = sandbox_root / "harness.py"

            candidate_path.write_text(candidate.source_code, encoding="utf-8")
            harness_path.write_text(
                _build_harness(spec=spec),
                encoding="utf-8",
            )

            case_results: list[JudgeCaseResult] = []
            last_stdout = ""
            last_stderr = ""
            last_exit_code: int | None = None

            for case_index, test_case in enumerate(spec.test_cases):
                result_path = sandbox_root / f"result-{case_index}.json"
                if result_path.exists():
                    result_path.unlink()

                wall_time_seconds = max(
                    spec.resource_limits.wall_time_seconds,
                    self._timeout_seconds,
                )
                try:
                    completed = subprocess.run(
                        [
                            sys.executable,
                            harness_path.name,
                            "--case-index",
                            str(case_index),
                            "--result-path",
                            result_path.name,
                        ],
                        cwd=sandbox_root,
                        capture_output=True,
                        text=True,
                        timeout=wall_time_seconds,
                        check=False,
                    )
                except subprocess.TimeoutExpired:
                    diagnostics = (
                        f"Case '{test_case.name}' exceeded the hard wall-clock limit "
                        f"of {wall_time_seconds:.1f}s.",
                    )
                    case_results.append(
                        JudgeCaseResult(
                            name=test_case.name,
                            outcome=TestingOutcome.TIME_LIMIT_EXCEEDED,
                            diagnostics=diagnostics,
                        )
                    )
                    return SandboxExecutionResult(
                        outcome=TestingOutcome.TIME_LIMIT_EXCEEDED,
                        diagnostics=diagnostics,
                        case_results=tuple(case_results),
                    )

                last_stdout = completed.stdout
                last_stderr = completed.stderr
                last_exit_code = completed.returncode

                if not result_path.exists():
                    if completed.returncode < 0 and spec.resource_limits.cpu_time_seconds > 0:
                        diagnostics = (
                            f"Case '{test_case.name}' exceeded the configured CPU limit "
                            "before the judge worker could emit a result.",
                        )
                        case_results.append(
                            JudgeCaseResult(
                                name=test_case.name,
                                outcome=TestingOutcome.TIME_LIMIT_EXCEEDED,
                                diagnostics=diagnostics,
                            )
                        )
                        return SandboxExecutionResult(
                            outcome=TestingOutcome.TIME_LIMIT_EXCEEDED,
                            diagnostics=diagnostics,
                            case_results=tuple(case_results),
                            stdout=completed.stdout,
                            stderr=completed.stderr,
                            exit_code=completed.returncode,
                        )
                    stderr = completed.stderr.strip()
                    diagnostics = ("Judge harness did not produce a structured result.",)
                    if stderr:
                        diagnostics = diagnostics + (stderr,)
                    return SandboxExecutionResult(
                        outcome=TestingOutcome.RUNTIME_ERROR,
                        diagnostics=diagnostics,
                        case_results=tuple(case_results),
                        stdout=completed.stdout,
                        stderr=completed.stderr,
                        exit_code=completed.returncode,
                    )

                payload = json.loads(result_path.read_text(encoding="utf-8"))
                current_case_results = tuple(
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
                )
                case_results.extend(current_case_results)
                outcome = TestingOutcome(payload["outcome"])
                if outcome is not TestingOutcome.PASSED:
                    return SandboxExecutionResult(
                        outcome=outcome,
                        diagnostics=tuple(payload.get("diagnostics", ())),
                        case_results=tuple(case_results),
                        stdout=payload.get("stdout", completed.stdout),
                        stderr=payload.get("stderr", completed.stderr),
                        exit_code=completed.returncode,
                    )

            return SandboxExecutionResult(
                outcome=TestingOutcome.PASSED,
                diagnostics=(
                    f"Judge accepted the candidate across {len(spec.test_cases)} case(s).",
                ),
                case_results=tuple(case_results),
                stdout=last_stdout,
                stderr=last_stderr,
                exit_code=last_exit_code,
            )


PythonSubprocessSandboxAdapter = PythonSubprocessJudgeAdapter


def _build_harness(*, spec: SandboxTestSpec) -> str:
    payload = {
        "entrypoint": spec.entrypoint,
        "test_cases": [_serialize_test_case(test_case) for test_case in spec.test_cases],
        "resource_limits": {
            "cpu_time_seconds": spec.resource_limits.cpu_time_seconds,
            "wall_time_seconds": spec.resource_limits.wall_time_seconds,
            "memory_limit_bytes": spec.resource_limits.memory_limit_bytes,
        },
    }
    payload_json = json.dumps(payload)
    return f"""import argparse
import contextlib
import importlib.util
import io
import json
import math
import sys
import tracemalloc
from pathlib import Path

try:
    import resource
except ImportError:
    resource = None

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


def apply_os_resource_limits():
    if resource is None:
        return

    cpu_limit = RESOURCE_LIMITS.get("cpu_time_seconds")
    if cpu_limit is not None and hasattr(resource, "RLIMIT_CPU"):
        hard_cpu_seconds = max(1, math.ceil(cpu_limit))
        resource.setrlimit(resource.RLIMIT_CPU, (hard_cpu_seconds, hard_cpu_seconds))

    memory_limit = RESOURCE_LIMITS.get("memory_limit_bytes")
    if memory_limit is not None and hasattr(resource, "RLIMIT_AS"):
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))


parser = argparse.ArgumentParser()
parser.add_argument("--case-index", type=int, required=True)
parser.add_argument("--result-path", required=True)
args = parser.parse_args()
RESULT_PATH = Path(args.result_path)
case = TEST_CASES[args.case_index]
case_results = []

apply_os_resource_limits()


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
except MemoryError:
    write_result({{
        "outcome": "memory_limit_exceeded",
        "diagnostics": ["Candidate import exceeded the configured memory limit."],
        "case_results": [{{
            "name": case["name"],
            "outcome": "memory_limit_exceeded",
            "diagnostics": ["Candidate import exceeded the configured memory limit."],
        }}],
    }})
    raise SystemExit(0)
except Exception as exc:
    write_result({{
        "outcome": "runtime_error",
        "diagnostics": [f"Module import failed: {{exc.__class__.__name__}}: {{exc}}."],
        "case_results": [{{
            "name": case["name"],
            "outcome": "runtime_error",
            "diagnostics": [f"Module import failed: {{exc.__class__.__name__}}: {{exc}}."],
        }}],
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
            f"Case '{{case['name']}}' exceeded the fallback traced memory limit: "
            f"{{peak_bytes}} > {{memory_limit}} bytes."
        ],
        "actual_output": value,
        "actual_stdout": captured_stdout,
    }})
    write_result({{
        "outcome": "memory_limit_exceeded",
        "diagnostics": [
            f"Case '{{case['name']}}' exceeded the fallback traced memory limit: "
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
    "diagnostics": [f"Judge accepted case '{{case['name']}}'."],
    "case_results": case_results,
    "stdout": captured_stdout,
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
