"""
src/agent.py — Core reasoning loop for ReClaw Scaffold.

Handles a single inbound message: loads persona context, searches memory for
relevant background, calls Claude via an OpenAI-compatible proxy, and
optionally saves notable responses to memory.
"""

import os
import logging
from pathlib import Path

import openai
from dotenv import load_dotenv

from memory import search_memory, write_memory, read_memory
from persona_router import load_soul

load_dotenv()
log = logging.getLogger("agent")

PROXY_URL = os.getenv("OPENCLAW_PROXY_URL", "http://127.0.0.1:3456")
MODEL = os.getenv("OPENCLAW_MODEL", "claude-opus-4-5")
WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


# ── Context loaders ───────────────────────────────────────────────────────────

def _load_template(name: str) -> str:
    """Load a template file from workspace/ or fall back to templates/."""
    workspace_path = WORKSPACE / name
    if workspace_path.exists():
        return workspace_path.read_text()
    fallback = TEMPLATES_DIR / name
    if fallback.exists():
        return fallback.read_text()
    return ""


def _build_system_prompt(persona_name: str, memory_snippets: list[str]) -> str:
    """Assemble the full system prompt from SOUL, AGENTS, USER, and memory."""
    soul = _load_template("SOUL.md")
    agents = _load_template("AGENTS.md")
    user = _load_template("USER.md")
    persona_soul = load_soul(persona_name)

    parts = []
    if soul:
        parts.append(f"# Agent Identity\n{soul}")
    if persona_soul:
        parts.append(f"# Persona: {persona_name}\n{persona_soul}")
    if agents:
        parts.append(f"# Operating Rules\n{agents}")
    if user:
        parts.append(f"# User Profile\n{user}")
    if memory_snippets:
        snippets_text = "\n\n".join(memory_snippets)
        parts.append(f"# Relevant Memory\n{snippets_text}")

    return "\n\n---\n\n".join(parts)


# ── Main entry point ──────────────────────────────────────────────────────────

def process_message(message: str, persona_name: str = "assistant") -> str:
    """
    Process a single user message and return the agent's response.

    1. Search memory for context relevant to this message.
    2. Build the system prompt from template files.
    3. Call Claude via the OpenAI-compatible proxy.
    4. Optionally save long responses to memory.
    """
    log.info("Processing message for persona=%s len=%d", persona_name, len(message))

    # 1. Retrieve relevant memory snippets
    memory_snippets = search_memory(message)

    # 2. Build system prompt
    system_prompt = _build_system_prompt(persona_name, memory_snippets)

    # 3. Call Claude via proxy
    try:
        client = openai.OpenAI(
            base_url=PROXY_URL,
            api_key=os.getenv("OPENCLAW_API_KEY", "not-needed"),  # proxy handles auth
        )
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        )
        response = completion.choices[0].message.content or ""
    except Exception as exc:
        log.error("LLM call failed: %s", exc)
        return f"[Agent error — could not reach model proxy at {PROXY_URL}]"

    # 4. Auto-save notable responses to memory
    if len(response) > 200:
        _maybe_save_to_memory(message, response)

    return response


def _maybe_save_to_memory(prompt: str, response: str) -> None:
    """Save a notable exchange to workspace/memory/conversations.md."""
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    snippet = (
        f"\n## {timestamp}\n"
        f"**User:** {prompt[:120]}{'...' if len(prompt) > 120 else ''}\n\n"
        f"**Agent:** {response[:400]}{'...' if len(response) > 400 else ''}\n"
    )
    try:
        write_memory("conversations.md", snippet)
        log.debug("Saved conversation snippet to memory/conversations.md")
    except Exception as exc:
        log.warning("Could not save to memory: %s", exc)
