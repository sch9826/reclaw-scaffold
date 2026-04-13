"""
workspace/autoresearch/judge.py — LLM-as-judge scorer.

Given a prompt, a response, and optional evaluation criteria, asks Claude to
score the response on a 1-10 scale and return structured reasoning.

Imported by orchestrator.py.
"""

import logging
import os
import sys
from pathlib import Path

import openai
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("judge")

# Allow imports from src/ when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

PROXY_URL = os.getenv("OPENCLAW_PROXY_URL", "http://127.0.0.1:3456")
MODEL = os.getenv("OPENCLAW_MODEL", "claude-opus-4-5")

JUDGE_SYSTEM_PROMPT = """You are an objective evaluator of AI assistant responses.

Your job: given a user prompt, an AI response, and optional evaluation criteria,
score the response on a scale of 1-10 and explain your reasoning.

Scoring rubric:
  9-10 — Excellent: accurate, complete, well-structured, appropriate tone
  7-8  — Good: mostly correct, minor gaps or style issues
  5-6  — Acceptable: correct but incomplete or awkward
  3-4  — Poor: partially wrong or significantly incomplete
  1-2  — Failing: wrong, harmful, or completely off-topic

Always respond in this exact JSON format:
{
  "score": <integer 1-10>,
  "reasoning": "<one paragraph explanation>"
}
"""


def score_response(prompt: str, response: str, criteria: str = "") -> dict:
    """
    Score a response using an LLM-as-judge approach.

    Args:
        prompt:   the original user prompt
        response: the agent's response to evaluate
        criteria: optional domain-specific criteria to apply

    Returns:
        dict with keys: score (int), reasoning (str)
    """
    criteria_section = f"\nAdditional criteria: {criteria}" if criteria else ""
    user_message = (
        f"Prompt: {prompt}\n\n"
        f"Response: {response}"
        f"{criteria_section}"
    )

    try:
        client = openai.OpenAI(
            base_url=PROXY_URL,
            api_key=os.getenv("OPENCLAW_API_KEY", "not-needed"),
        )
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,  # deterministic scoring
        )
        raw = completion.choices[0].message.content or "{}"
        import json
        parsed = json.loads(raw)
        return {
            "score": int(parsed.get("score", 0)),
            "reasoning": parsed.get("reasoning", ""),
        }
    except Exception as exc:
        log.error("Judge call failed: %s", exc)
        return {"score": 0, "reasoning": f"Judge error: {exc}"}
