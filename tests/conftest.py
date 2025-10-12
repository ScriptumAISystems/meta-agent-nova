"""Pytest configuration for bridge tests."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path


def _install_fastapi_shim() -> None:
    """Expose the lightweight FastAPI shim under the ``fastapi`` namespace."""

    shim = import_module("tests.fastapi_shim")
    testclient = import_module("tests.fastapi_shim.testclient")

    sys.modules.setdefault("fastapi", shim)
    sys.modules.setdefault("fastapi.testclient", testclient)

    # Ensure attribute-based access (``fastapi.testclient``) works on the shim module.
    setattr(shim, "testclient", testclient)



ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_install_fastapi_shim()
