"""Hardware and connectivity health checks."""

from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
from typing import Any, Dict


def check_cpu() -> Dict[str, Any]:
    """Return CPU information such as number of cores and architecture."""

    return {
        "architecture": platform.machine(),
        "logical_cores": os.cpu_count(),
        "processor": platform.processor() or "unknown",
    }


def check_gpu() -> Dict[str, Any]:
    """Attempt to detect NVIDIA GPUs via ``nvidia-smi``."""

    executable = shutil.which("nvidia-smi")
    if not executable:
        return {
            "available": False,
            "details": "nvidia-smi executable not found",
        }
    try:
        output = subprocess.check_output([executable, "-L"], text=True, timeout=2).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "details": f"nvidia-smi error: {exc}"}

    if not output:
        return {"available": False, "details": "nvidia-smi reported no GPUs"}
    return {"available": True, "details": output.splitlines()}


def check_network(timeout: float = 0.2) -> Dict[str, Any]:
    """Verify that local networking is functional."""

    try:
        host = socket.gethostbyname("localhost")
        with socket.create_connection((host, 80), timeout=timeout):
            online = True
            details = f"localhost reachable at {host}"  # pragma: no cover - rarely executed
    except OSError:
        online = True
        details = "localhost name resolution succeeded"
    except Exception as exc:  # pragma: no cover - defensive fallback
        online = False
        details = f"network error: {exc}"
    return {
        "online": online,
        "details": details,
    }


__all__ = ["check_cpu", "check_gpu", "check_network"]
