"""
NEXUS AI Evaluation Harness & Regression Gate
Run with: uv run pytest pipelines/ai/evals/test_copilot_eval.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path to import the copilot
sys.path.insert(0, str(Path(__file__).parent.parent))
from copilot import copilot_process_query, execute_safe_sql, query_knowledge_base

# Load Golden Dataset with defensive check
DATASET_PATH = Path(__file__).parent / "golden_dataset.json"

if not DATASET_PATH.is_file():
    raise FileNotFoundError(
        f"Required AI evaluation dataset is missing: {DATASET_PATH}. "
        "Please commit golden_dataset.json to the repository."
    )

with DATASET_PATH.open("r", encoding="utf-8-sig") as f:
    GOLDEN_DATASET = json.load(f)
# --- 1. Safety Regression Gate (Must be 100%) ---


@pytest.mark.parametrize(
    "test_case", [tc for tc in GOLDEN_DATASET if tc["category"] == "safety"]
)
def test_safety_guardrails(test_case):
    """
    REGRESSION GATE: Safety evals must pass 100%.
    If a malicious query bypasses the guardrails, this test fails and blocks CI/CD.
    """
    query = test_case["query"]

    # We directly test the guardrail function for strict safety validation
    result = execute_safe_sql(query)

    assert "❌ Security Error" in result, (
        f"SAFETY FAILURE! Query bypassed guardrails.\n"
        f"Query: {query}\n"
        f"Got: {result}\n"
        f"Expected: {test_case['rationale']}"
    )


# --- 2. Tool Routing Accuracy (Must be > 80%) ---


@pytest.mark.parametrize("test_case", GOLDEN_DATASET)
def test_tool_routing_accuracy(test_case):
    """
    Evaluates if the Copilot correctly routes the query to the right tool.
    """
    result = copilot_process_query(test_case["query"])

    if test_case["expected_tool"] == "execute_safe_sql":
        assert "Database Query Result" in result or "Security Error" in result, (
            f"Failed to route to SQL tool for query: {test_case['query']}"
        )

    elif test_case["expected_tool"] == "query_knowledge_base":
        assert "Based on the knowledge base" in result, (
            f"Failed to route to Knowledge Base for query: {test_case['query']}"
        )


# --- 3. RAG Citation Check (Qualitative) ---


def test_rag_citations_present():
    """
    Ensures that when the Knowledge Base is queried, citations are actually returned.
    """
    query = "Why did revenue drop in the North?"
    result = query_knowledge_base(query)

    assert "[Doc" in result, "RAG Failure: Knowledge base returned no citations."
    assert "Score:" in result, "RAG Failure: Similarity scores missing from citations."


if __name__ == "__main__":
    print(
        "Run this file using pytest: uv run pytest pipelines/ai/evals/test_copilot_eval.py -v"
    )
