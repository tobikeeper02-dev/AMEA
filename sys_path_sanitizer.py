"""Utilities to harden sys.path against numpy source-tree collisions."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable


def _looks_like_numpy_source(base: Path) -> bool:
    """Return True if *base* appears to be a numpy source checkout.

    We look for common markers like ``setup.py`` or ``pyproject.toml`` and also
    treat directories named ``numpy`` that contain a ``.git`` folder as source
    trees. Installed numpy wheels under ``site-packages`` typically lack these
    markers, so they are preserved.
    """

    markers: Iterable[str] = ("setup.py", "pyproject.toml", ".git")
    if base.name != "numpy":
        return False
    return any((base / marker).exists() for marker in markers)


def sanitize_numpy_source_paths() -> None:
    """Prune numpy source directories from ``sys.path``.

    Streamlit sessions can inherit environment-specific ``PYTHONPATH`` entries or
    working directories that unintentionally point at a numpy checkout. When that
    happens, ``pandas`` raises "do not import from the numpy source tree". We
    defensively remove any sys.path entries that look like numpy source folders,
    as well as parent directories that directly contain such folders.
    """

    cleaned: list[str] = []
    for entry in list(sys.path):
        try:
            base = Path(entry or ".").resolve()
        except OSError:
            cleaned.append(entry)
            continue

        if _looks_like_numpy_source(base):
            continue

        potential_child = base / "numpy"
        if _looks_like_numpy_source(potential_child):
            continue

        cleaned.append(entry)

    if cleaned != sys.path:
        sys.path[:] = cleaned


__all__ = ["sanitize_numpy_source_paths"]
