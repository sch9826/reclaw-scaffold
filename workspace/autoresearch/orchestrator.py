"""
workspace/autoresearch/orchestrator.py — Overnight optimization loop.

Runs a suite of test cases through the agent, scores them with the LLM-as-
judge, and writes a summary report to workspace/autoresearch/logs/.

Designed to be triggered by a systemd timer (reclaw-autoresearch.timer) so it
runs while you sleep and you wake up to a report.

Usage:
    python workspace/autoresearch/orchestrator.py
    python workspace/autoresearch/orchestrator.py --test-file test_cases/general.json
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Allow imports from src/ when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from evaluate import run_evaluation
from judge import score_response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("orchestrator")

AUTORESEARCH_DIR = Path(__file__).resolve().parent
LOGS_DIR = AUTORESEARCH_DIR / "logs"
DEFAULT_TEST_FILE = AUTORESEARCH_DIR / "test_cases" / "general.json"


def load_test_cases(path: Path) -> list[dict]:
    """Load test cases from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    log.info("Loaded %d test cases from %s", len(data), path)
    return data


def run_overnight(test_file: Path = DEFAULT_TEST_FILE) -> dict:
    """
    Run all test cases, score results, and write a log report.

    Returns a summary dict with pass_count, fail_count, avg_score.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = LOGS_DIR / f"autoresearch_{timestamp}.json"

    test_cases = load_test_cases(test_file)
    results = []

    for i, case in enumerate(test_cases, 1):
        log.info("Running test %d/%d: %s", i, len(test_cases), case.get("name", "unnamed"))
        try:
            response = run_evaluation(case)
            score = score_response(
                prompt=case["prompt"],
                response=response,
                criteria=case.get("criteria", ""),
            )
            result = {
                "name": case.get("name", f"test_{i}"),
                "prompt": case["prompt"],
                "response": response,
                "score": score["score"],
                "reasoning": score["reasoning"],
                "passed": score["score"] >= case.get("min_score", 7),
            }
        except Exception as exc:
            log.error("Test %d failed with exception: %s", i, exc)
            result = {
                "name": case.get("name", f"test_{i}"),
                "prompt": case["prompt"],
                "response": None,
                "score": 0,
                "reasoning": str(exc),
                "passed": False,
            }
        results.append(result)

    # Summarize
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0

    summary = {
        "timestamp": timestamp,
        "test_file": str(test_file),
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "avg_score": round(avg_score, 2),
        "results": results,
    }

    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)

    log.info(
        "Autoresearch complete — %d/%d passed, avg score %.1f — report: %s",
        len(passed),
        len(results),
        avg_score,
        report_path,
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Overnight autoresearch loop")
    parser.add_argument(
        "--test-file",
        type=Path,
        default=DEFAULT_TEST_FILE,
        help="Path to a JSON file containing test cases",
    )
    args = parser.parse_args()
    summary = run_overnight(args.test_file)
    print(f"\nResult: {summary['passed']}/{summary['total']} passed, avg score {summary['avg_score']}")
