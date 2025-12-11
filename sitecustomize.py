"""Startup hook to keep numpy source checkouts off sys.path."""
from __future__ import annotations

from sys_path_sanitizer import sanitize_numpy_source_paths

sanitize_numpy_source_paths()
