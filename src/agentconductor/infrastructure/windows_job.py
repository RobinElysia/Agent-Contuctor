"""Windows Job Object helpers for judge worker resource enforcement."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from dataclasses import dataclass
from typing import Protocol

from agentconductor.domain.execution import JudgeResourceLimits, TestingOutcome


_INFINITE = 0xFFFFFFFF
_WAIT_OBJECT_0 = 0x00000000
_JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_SYNCHRONIZE = 0x00100000
_STATUS_NO_MEMORY = 0xC0000017


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", _IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


@dataclass(slots=True)
class BoundProcessContext:
    """Metadata about platform-specific resource binding for one worker."""

    platform: str
    hard_memory_limit: bool
    hard_cpu_limit: bool
    hard_wall_time_limit: bool
    assigned_to_job: bool = False
    memory_limit_bytes: int | None = None
    peak_process_memory_used: int | None = None
    binding_diagnostics: tuple[str, ...] = ()
    _kernel32: ctypes.WinDLL | None = None
    _job_handle: int | None = None
    _process_handle: int | None = None

    def classify_missing_result(self, *, return_code: int | None) -> tuple[TestingOutcome | None, tuple[str, ...]]:
        """Classify a worker exit when the harness produced no structured result."""
        if (
            self.platform == "win32"
            and self.assigned_to_job
            and self.hard_memory_limit
            and self.memory_limit_bytes is not None
        ):
            if return_code == _STATUS_NO_MEMORY:
                return (
                    TestingOutcome.MEMORY_LIMIT_EXCEEDED,
                    (
                        "Windows Job Object enforcement rejected the worker with a no-memory exit.",
                    ),
                )
            if (
                self.peak_process_memory_used is not None
                and self.peak_process_memory_used >= self.memory_limit_bytes
            ):
                return (
                    TestingOutcome.MEMORY_LIMIT_EXCEEDED,
                    (
                        "Windows Job Object enforcement stopped the worker near the configured process memory limit before the harness emitted a result.",
                    ),
                )
        return None, ()

    def observe_process_exit(self) -> None:
        """Capture post-exit Windows Job Object accounting before teardown."""
        if (
            self.platform != "win32"
            or self._kernel32 is None
            or self._process_handle is None
        ):
            return
        self._kernel32.WaitForSingleObject(self._process_handle, _INFINITE)
        if self._job_handle is not None:
            self.peak_process_memory_used = self._query_peak_process_memory()

    def close(self) -> None:
        """Release native handles owned by the binding context."""
        if self._kernel32 is not None and self._job_handle is not None:
            self._kernel32.CloseHandle(self._job_handle)
            self._job_handle = None
        if self._kernel32 is not None and self._process_handle is not None:
            self._kernel32.CloseHandle(self._process_handle)
            self._process_handle = None

    def _query_peak_process_memory(self) -> int | None:
        if self._kernel32 is None or self._job_handle is None:
            return None
        limit_info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        if not self._kernel32.QueryInformationJobObject(
            self._job_handle,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limit_info),
            ctypes.sizeof(limit_info),
            None,
        ):
            return None
        return int(limit_info.PeakProcessMemoryUsed)


class ProcessLimitBinder(Protocol):
    """Attach platform-specific process resource controls."""

    def bind(
        self,
        *,
        process_pid: int,
        resource_limits: JudgeResourceLimits,
    ) -> BoundProcessContext:
        """Attach resource controls to the newly created worker process."""


class NoOpProcessLimitBinder:
    """Fallback binder used when no platform-specific binding is needed."""

    def bind(
        self,
        *,
        process_pid: int,
        resource_limits: JudgeResourceLimits,
    ) -> BoundProcessContext:
        del process_pid, resource_limits
        return BoundProcessContext(
            platform=sys.platform,
            hard_memory_limit=False,
            hard_cpu_limit=False,
            hard_wall_time_limit=False,
        )


class WindowsJobObjectBinder:
    """Bind a process into a Job Object with hard Windows memory limits."""

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise RuntimeError("WindowsJobObjectBinder is only available on Windows.")
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._configure_signatures()

    def bind(
        self,
        *,
        process_pid: int,
        resource_limits: JudgeResourceLimits,
    ) -> BoundProcessContext:
        access = _PROCESS_QUERY_LIMITED_INFORMATION | _SYNCHRONIZE
        process_handle = self._kernel32.OpenProcess(access, False, process_pid)
        if not process_handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if resource_limits.memory_limit_bytes is None:
                return BoundProcessContext(
                    platform="win32",
                    hard_memory_limit=False,
                    hard_cpu_limit=False,
                    hard_wall_time_limit=False,
                    _kernel32=self._kernel32,
                    _process_handle=process_handle,
                    binding_diagnostics=(
                        "Windows Job Object binder skipped hard memory enforcement because no memory limit was configured.",
                    ),
                )

            job_handle = self._kernel32.CreateJobObjectW(None, None)
            if not job_handle:
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                limit_info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
                limit_info.BasicLimitInformation.LimitFlags = (
                    _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | _JOB_OBJECT_LIMIT_PROCESS_MEMORY
                )
                limit_info.ProcessMemoryLimit = resource_limits.memory_limit_bytes
                if not self._kernel32.SetInformationJobObject(
                    job_handle,
                    _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                    ctypes.byref(limit_info),
                    ctypes.sizeof(limit_info),
                ):
                    raise ctypes.WinError(ctypes.get_last_error())
                if not self._kernel32.AssignProcessToJobObject(job_handle, process_handle):
                    bind_error = ctypes.WinError(ctypes.get_last_error())
                    if getattr(bind_error, "winerror", None) == 5:
                        self._kernel32.CloseHandle(job_handle)
                        return BoundProcessContext(
                            platform="win32",
                            hard_memory_limit=False,
                            hard_cpu_limit=False,
                            hard_wall_time_limit=False,
                            assigned_to_job=False,
                            memory_limit_bytes=resource_limits.memory_limit_bytes,
                            binding_diagnostics=(
                                "Windows Job Object binding was unavailable in this host runtime; wall-clock enforcement remains active but hard memory enforcement could not be attached.",
                            ),
                            _kernel32=self._kernel32,
                            _process_handle=process_handle,
                        )
                    raise bind_error

                return BoundProcessContext(
                    platform="win32",
                    hard_memory_limit=True,
                    hard_cpu_limit=False,
                    hard_wall_time_limit=False,
                    assigned_to_job=True,
                    memory_limit_bytes=resource_limits.memory_limit_bytes,
                    binding_diagnostics=(
                        "Windows Job Object enforced a per-process memory limit.",
                    ),
                    _kernel32=self._kernel32,
                    _job_handle=job_handle,
                    _process_handle=process_handle,
                )
            except Exception:
                self._kernel32.CloseHandle(job_handle)
                raise
        except Exception:
            self._kernel32.CloseHandle(process_handle)
            raise

    def _configure_signatures(self) -> None:
        self._kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE

        self._kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self._kernel32.CreateJobObjectW.restype = wintypes.HANDLE

        self._kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        self._kernel32.SetInformationJobObject.restype = wintypes.BOOL

        self._kernel32.AssignProcessToJobObject.argtypes = [
            wintypes.HANDLE,
            wintypes.HANDLE,
        ]
        self._kernel32.AssignProcessToJobObject.restype = wintypes.BOOL

        self._kernel32.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.c_void_p,
        ]
        self._kernel32.QueryInformationJobObject.restype = wintypes.BOOL

        self._kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._kernel32.WaitForSingleObject.restype = wintypes.DWORD

        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL


def build_process_limit_binder() -> ProcessLimitBinder:
    """Return the platform-aware process limit binder for judge workers."""
    if sys.platform == "win32":
        return WindowsJobObjectBinder()
    return NoOpProcessLimitBinder()
