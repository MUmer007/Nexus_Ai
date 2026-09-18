"""
NEXUS AI Evaluation Harness & Regression Gate
Run with: uv run pytest pipelines/ai/evals/test_copilot_eval.py -v
"""

import json
import sys
import time
from pathlib import Path

import pytest
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

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


# --- Setup Qdrant for CI Testing (with retries) ---
@pytest.fixture(scope="session", autouse=True)
def setup_qdrant_test_data():
    """Initialize Qdrant collection and upsert test documents for RAG tests."""
    client = QdrantClient(url="http://localhost:6333", timeout=10)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    collection_name = "nexus_knowledge_base"

    # Retry loop to wait for Qdrant service to be ready in CI
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Check if we can ping Qdrant
            client.get_collections()
            break  # Success!
        except (ConnectionError, TimeoutError, OSError) as exc:
            if attempt == max_retries - 1:
                raise RuntimeError(
                    "Failed to connect to Qdrant after 5 attempts."
                ) from exc
            time.sleep(2)  # Wait 2 seconds before retrying

    # Ensure clean state
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )

    # Upsert test documents
    documents = [
        {
            "id": 1,
            "text": "Revenue dropped in the North region last week due to supplier delays.",
        },
        {
            "id": 2,
            "text": "Premium customers have a 15% higher delivery delay rate on weekends.",
        },
        {
            "id": 3,
            "text": "The new inventory allocation policy reduced stockouts by 20%.",
        },
    ]

    points = []
    for doc in documents:
        vector = model.encode(doc["text"]).tolist()
        points.append(
            models.PointStruct(
                id=doc["id"], vector=vector, payload={"text": doc["text"]}
            )
        )

    client.upsert(collection_name=collection_name, points=points)
    yield


# --- 1. Safety Regression Gate (Must be 100%) ---
@pytest.mark.parametrize(
    "test_case", [tc for tc in GOLDEN_DATASET if tc["category"] == "safety"]
)
def test_safety_guardrails(test_case):
    query = test_case["query"]
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
    query = "Why did revenue drop in the North?"
    result = query_knowledge_base(query)

    assert "[Doc" in result, "RAG Failure: Knowledge base returned no citations."
    assert "Score:" in result, "RAG Failure: Similarity scores missing from citations."


if __name__ == "__main__":
    print(
        "Run this file using pytest: uv run pytest pipelines/ai/evals/test_copilot_eval.py -v"
    )
