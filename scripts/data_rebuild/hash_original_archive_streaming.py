#!/usr/bin/env python3
"""Memory-bounded full-file SHA-256 for immutable original research archives.

Never use Path.read_bytes() to hash potentially large original frozen ZIPs:
that materializes the entire binary archive at once, possibly exhausting RAM.
The caller must still check this digest against an externally pinned,
scientifically vetted original SHA-256 before reading original data members.
This module does not establish source validity or access any ZIP contents.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path, chunk_bytes: int = 1 << 20) -> str:
    """Compute SHA-256 over the exact original byte stream in bounded memory."""
    if chunk_bytes < 1:
        raise ValueError("SHA-256 file chunk size must be positive")
    hasher = hashlib.sha256()
    with Path(path).open("rb") as source:
        while True:
            data = source.read(chunk_bytes)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()
