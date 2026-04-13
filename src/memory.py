"""
src/memory.py — Flat-file memory layer for ReClaw Scaffold.

All memory lives in workspace/memory/ as plain Markdown files.  No vector
database required — search is a simple keyword scan across all files.
"""

import logging
from pathlib import Path

log = logging.getLogger("memory")

MEMORY_DIR = Path(__file__).resolve().parent.parent / "workspace" / "memory"


def _ensure_dir() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


# ── Read ──────────────────────────────────────────────────────────────────────

def read_memory(filename: str) -> str:
    """
    Read the full contents of workspace/memory/<filename>.
    Returns an empty string if the file does not exist.
    """
    _ensure_dir()
    path = MEMORY_DIR / filename
    if not path.exists():
        log.debug("Memory file not found: %s", filename)
        return ""
    return path.read_text()


# ── Write ─────────────────────────────────────────────────────────────────────

def write_memory(filename: str, content: str, mode: str = "a") -> None:
    """
    Write or append to workspace/memory/<filename>.

    Args:
        filename: basename of the file (e.g. "tasks.md")
        content:  text to write
        mode:     "a" to append (default) or "w" to overwrite
    """
    _ensure_dir()
    path = MEMORY_DIR / filename
    with open(path, mode) as f:
        f.write(content)
    log.debug("Wrote to memory/%s (mode=%s, len=%d)", filename, mode, len(content))


# ── List ──────────────────────────────────────────────────────────────────────

def list_memory() -> list[str]:
    """Return the basenames of all files in workspace/memory/."""
    _ensure_dir()
    return sorted(p.name for p in MEMORY_DIR.iterdir() if p.is_file())


# ── Search ────────────────────────────────────────────────────────────────────

def search_memory(query: str, top_k: int = 3) -> list[str]:
    """
    Naive keyword search across all memory files.

    Splits the query into words and scores each paragraph-sized chunk by how
    many query words appear in it (case-insensitive).  Returns the top_k
    highest-scoring chunks as strings.

    This is intentionally simple — no embeddings, no vector DB.  For most
    personal-agent use cases keyword search is sufficient and zero-dependency.
    """
    _ensure_dir()
    words = [w.lower() for w in query.split() if len(w) > 2]
    if not words:
        return []

    candidates: list[tuple[int, str]] = []

    for path in MEMORY_DIR.iterdir():
        if not path.is_file():
            continue
        text = path.read_text()
        # Split into ~paragraph chunks (blank-line separated)
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        for chunk in chunks:
            chunk_lower = chunk.lower()
            score = sum(1 for w in words if w in chunk_lower)
            if score > 0:
                label = f"[{path.name}]\n{chunk}"
                candidates.append((score, label))

    # Sort descending by score, return top_k
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [text for _, text in candidates[:top_k]]
