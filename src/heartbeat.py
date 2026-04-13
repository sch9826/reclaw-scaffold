"""
src/heartbeat.py — Proactive heartbeat checker for ReClaw Scaffold.

Fires every 30 minutes (scheduled by main.py).  If nothing actionable is
found, it logs HEARTBEAT_OK and stays silent.  If open tasks or flagged items
are detected, it sends a Discord message to the configured channel.
"""

import os
import logging
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("heartbeat")

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
HEARTBEAT_LOG = MEMORY_DIR / "heartbeat.log"
TASKS_FILE = MEMORY_DIR / "tasks.md"
DISCORD_HEARTBEAT_CHANNEL = os.getenv("DISCORD_HEARTBEAT_CHANNEL", "")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")


# ── Core check ────────────────────────────────────────────────────────────────

def _read_open_tasks() -> list[str]:
    """
    Parse workspace/memory/tasks.md for lines beginning with '- [ ]'.
    Returns a list of open task strings (empty list if file absent).
    """
    if not TASKS_FILE.exists():
        return []
    lines = TASKS_FILE.read_text().splitlines()
    return [line.strip() for line in lines if line.strip().startswith("- [ ]")]


def _read_flagged_items() -> list[str]:
    """
    Scan the last 50 lines of heartbeat.log for FLAGGED: entries added
    by previous heartbeat runs.
    """
    if not HEARTBEAT_LOG.exists():
        return []
    lines = HEARTBEAT_LOG.read_text().splitlines()[-50:]
    return [line for line in lines if "FLAGGED:" in line]


def _log_heartbeat(message: str) -> None:
    """Append a timestamped line to heartbeat.log."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HEARTBEAT_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def _send_discord_message(text: str) -> None:
    """Post a message to the designated Discord heartbeat channel via REST API."""
    if not DISCORD_HEARTBEAT_CHANNEL or not DISCORD_BOT_TOKEN:
        log.warning(
            "DISCORD_HEARTBEAT_CHANNEL or DISCORD_BOT_TOKEN not set — "
            "cannot send proactive message."
        )
        return

    url = f"https://discord.com/api/v10/channels/{DISCORD_HEARTBEAT_CHANNEL}/messages"
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}", "Content-Type": "application/json"}
    payload = {"content": text}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        log.info("Sent heartbeat message to channel %s", DISCORD_HEARTBEAT_CHANNEL)
    except Exception as exc:
        log.error("Failed to send Discord heartbeat message: %s", exc)


# ── Public interface ──────────────────────────────────────────────────────────

def run_heartbeat() -> None:
    """
    Main heartbeat function — call this every 30 minutes.

    Contract:
      - If nothing actionable → log HEARTBEAT_OK, stay silent.
      - If actionable items found → log HEARTBEAT_ALERT, send Discord message.
    """
    open_tasks = _read_open_tasks()
    flagged = _read_flagged_items()

    if not open_tasks and not flagged:
        _log_heartbeat("HEARTBEAT_OK — no open tasks, no flagged items")
        log.info("HEARTBEAT_OK")
        return

    # Build alert message
    lines = ["**Heartbeat Alert** — items need your attention:"]
    if open_tasks:
        lines.append(f"\n**Open tasks ({len(open_tasks)}):**")
        for task in open_tasks[:5]:  # cap at 5 to avoid spam
            lines.append(f"  {task}")
        if len(open_tasks) > 5:
            lines.append(f"  … and {len(open_tasks) - 5} more")
    if flagged:
        lines.append(f"\n**Previously flagged ({len(flagged)}):**")
        for item in flagged[-3:]:
            lines.append(f"  {item}")

    alert_text = "\n".join(lines)
    _log_heartbeat(f"HEARTBEAT_ALERT — {len(open_tasks)} open tasks, {len(flagged)} flagged items")
    log.info("HEARTBEAT_ALERT — sending to Discord")
    _send_discord_message(alert_text)
