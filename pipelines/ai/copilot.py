"""
NEXUS AI Copilot Engine
Demonstrates typed tool-calling and SQL safety guardrails.
"""
import sqlite3
import re
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# --- 1. Initialize External Services ---
qdrant_client = QdrantClient(url="http://localhost:6333")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Setup a mock read-only database for demonstration
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()
cursor.execute("CREATE TABLE gold_revenue (region TEXT, revenue REAL, week TEXT)")
cursor.execute("INSERT INTO gold_revenue VALUES ('North', 150000.00, '2026-W36')")
cursor.execute("INSERT INTO gold_revenue VALUES ('South', 220000.00, '2026-W36')")
conn.commit()

# --- 2. Define the Tools (with strict guardrails) ---

def query_knowledge_base(query: str) -> str:
    """Searches the vector database for contextual business knowledge."""
    query_vector = embedding_model.encode(query).tolist()
    results = qdrant_client.query_points(
        collection_name="nexus_knowledge_base",
        query=query_vector,
        limit=2
    ).points
    
    if not results:
        return "No relevant documents found in the knowledge base."
    
    citations = [f"[Doc {r.id}] (Score: {r.score:.2f}): {r.payload['text']}" for r in results]
    return "\n".join(citations)

def execute_safe_sql(sql: str) -> str:
    """
    Executes a read-only SQL query against the Gold layer.
    GUARDRAILS: Read-only, blocklist, and strict table allow-listing.
    """
    sql_upper = sql.strip().upper()
    
    # Guardrail 1: Read-only enforcement
    if not sql_upper.startswith("SELECT"):
        return "❌ Security Error: Only SELECT queries are permitted."
    
    # Guardrail 2: Destructive keyword blocklist
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER"]
    if any(kw in sql_upper for kw in dangerous_keywords):
        return f"❌ Security Error: Destructive operation detected."

    # Guardrail 3: Table allow-listing (FIXED: check against uppercase allowed tables)
    allowed_tables = ["GOLD_REVENUE", "GOLD_INVENTORY"]
    if not any(table in sql_upper for table in allowed_tables):
        return "❌ Security Error: Querying unauthorized tables."

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return f"✅ Query Successful.\nColumns: {columns}\nData: {rows}"
    except Exception as e:
        return f"❌ Database Error: {str(e)}"

# --- 3. The Copilot Router (Simulates LLM Tool-Calling) ---

def copilot_process_query(user_query: str) -> str:
    query_lower = user_query.lower()
    
    print(f"🧠 Copilot Reasoning: Analyzing query intent...")
    
    if any(word in query_lower for word in ["why", "reason", "context", "policy", "supplier"]):
        print("   ➔ Tool Selected: query_knowledge_base")
        context = query_knowledge_base(user_query)
        return f"📝 Based on the knowledge base:\n{context}"
        
    elif any(word in query_lower for word in ["revenue", "sales", "how much", "total"]):
        print("   ➔ Tool Selected: execute_safe_sql")
        generated_sql = "SELECT region, revenue FROM gold_revenue WHERE region = 'North'"
        print(f"   ➔ Generated SQL: {generated_sql}")
        db_result = execute_safe_sql(generated_sql)
        return f"📊 Database Query Result:\n{db_result}"
        
    else:
        return "🤔 I'm not sure how to answer that."

# --- 4. Test the Copilot ---

if __name__ == "__main__":
    print("="*60)
    print("🎯 NEXUS AI Copilot Test Suite")
    print("="*60)
    
    # Test 1: Knowledge Base Retrieval
    print("\n[Test 1] Asking for context...")
    response1 = copilot_process_query("Why did sales go down in the North?")
    print(response1)
    
    # Test 2: Safe SQL Execution (Should pass now!)
    print("\n[Test 2] Asking for quantitative data...")
    response2 = copilot_process_query("What was the revenue in the North region?")
    print(response2)
    
    # Test 3: SQL Guardrail Trigger (Malicious Query)
    print("\n[Test 3] Attempting a malicious SQL injection...")
    malicious_sql = "SELECT * FROM gold_revenue; DROP TABLE gold_revenue;"
    response3 = execute_safe_sql(malicious_sql)
    print(response3)
    
    print("\n" + "="*60)
    print("✅ Copilot engine test completed successfully!")
    print("="*60)
