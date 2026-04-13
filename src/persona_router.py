"""
src/persona_router.py — Channel-to-persona routing for ReClaw Scaffold.

Loads workspace/persona_routing.json (Discord channel_id → persona_name) and
provides helpers to look up which persona should respond in a given channel,
and to load that persona's soul file if one exists.
"""

import json
import logging
from pathlib import Path

log = logging.getLogger("persona_router")

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
ROUTING_FILE = WORKSPACE / "persona_routing.json"
SOULS_DIR = WORKSPACE / "souls"

DEFAULT_PERSONA = "assistant"

# Cache the routing table at module load time
_routing: dict[str, str] = {}


def _load_routing() -> dict[str, str]:
    """Load persona_routing.json from workspace/.  Returns {} if absent."""
    global _routing
    if _routing:
        return _routing
    if not ROUTING_FILE.exists():
        log.info(
            "persona_routing.json not found at %s — all channels will use "
            "default persona '%s'",
            ROUTING_FILE,
            DEFAULT_PERSONA,
        )
        _routing = {}
        return _routing
    try:
        _routing = json.loads(ROUTING_FILE.read_text())
        log.info("Loaded %d persona routing entries", len(_routing))
    except Exception as exc:
        log.error("Failed to parse persona_routing.json: %s", exc)
        _routing = {}
    return _routing


# ── Public API ────────────────────────────────────────────────────────────────

def get_persona(channel_id: str) -> str:
    """
    Return the persona name mapped to channel_id.
    Falls back to DEFAULT_PERSONA ("assistant") if no mapping exists.
    """
    routing = _load_routing()
    persona = routing.get(str(channel_id), DEFAULT_PERSONA)
    log.debug("channel=%s → persona=%s", channel_id, persona)
    return persona


def load_soul(persona_name: str) -> str:
    """
    Read workspace/souls/<persona_name>.md if it exists.
    Returns an empty string if no per-persona soul file is present — the
    agent will fall back to the global SOUL.md template instead.
    """
    soul_path = SOULS_DIR / f"{persona_name}.md"
    if soul_path.exists():
        log.debug("Loaded soul for persona=%s", persona_name)
        return soul_path.read_text()
    return ""
