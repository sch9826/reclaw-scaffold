"""
workspace/autoresearch/evaluate.py — Test case runner.

Sends a single test case prompt to the agent and returns the raw response
string.  Imported by orchestrator.py.
"""

import logging
import sys
from pathlib import Path

# Allow imports from src/ when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from agent import process_message

log = logging.getLogger("evaluate")


def run_evaluation(test_case: dict) -> str:
    """
    Run a single test case through the agent.

    Expected test_case keys:
      - prompt (str, required): the user message to send
      - persona (str, optional): persona name to use, defaults to "assistant"
      - name (str, optional): human-readable label for logging

    Returns the agent's response as a string.
    """
    prompt = test_case["prompt"]
    persona = test_case.get("persona", "assistant")
    name = test_case.get("name", "unnamed")

    log.info("Evaluating: %s (persona=%s)", name, persona)
    response = process_message(prompt, persona)
    log.debug("Response len=%d", len(response or ""))
    return response or ""
