"""Shared private-output boundary check, matching the canonical runner.

An empty marker directory is not a Git repository. Actual repository HEADs,
worktree marker files, and symlinked markers are conservatively rejected.
"""
from pathlib import Path


def under_git(path: Path) -> bool:
    path=Path(path).resolve()
    return any(marker.is_symlink() or marker.is_file() or (marker.is_dir() and (marker/"HEAD").is_file())
               for node in (path,*path.parents) for marker in (node/".git",))
