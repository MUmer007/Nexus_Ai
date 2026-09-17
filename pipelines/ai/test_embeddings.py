"""
Test script to generate embeddings and store/retrieve them from Qdrant.
Updated for qdrant-client >= 1.9.0 and sentence-transformers >= 3.0.0
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# 1. Initialize Qdrant client (pointing to local Docker container)
print("🔌 Connecting to Qdrant...")
client = QdrantClient(url="http://localhost:6333")

# 2. Initialize the embedding model
print("🧠 Loading embedding model (all-MiniLM-L6-v2)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Create a collection in Qdrant (using modern API)
collection_name = "nexus_knowledge_base"
vector_size = model.get_embedding_dimension()  # Updated method name

print(f"📦 Setting up collection '{collection_name}' with vector size {vector_size}...")
if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(
        size=vector_size, distance=models.Distance.COSINE
    ),
)

# 4. Sample data to embed (simulating business knowledge)
documents = [
    {
        "id": 1,
        "text": "Revenue dropped in the North region last week due to supplier delays.",
    },
    {
        "id": 2,
        "text": "Premium customers have a 15% higher delivery delay rate on weekends.",
    },
    {"id": 3, "text": "The new inventory allocation policy reduced stockouts by 20%."},
]

# 5. Generate embeddings and upsert into Qdrant
print("📝 Generating embeddings and upserting to Qdrant...")
points = []
for doc in documents:
    vector = model.encode(doc["text"]).tolist()
    points.append(
        models.PointStruct(id=doc["id"], vector=vector, payload={"text": doc["text"]})
    )

client.upsert(collection_name=collection_name, points=points)
print("✅ Successfully upserted 3 documents into Qdrant!")

# 6. Perform a similarity search
query_text = "Why did sales go down in the North?"
print(f"\n🔍 Searching for: '{query_text}'")

query_vector = model.encode(query_text).tolist()

# Search Qdrant using the modern query_points API
search_results = client.query_points(
    collection_name=collection_name, query=query_vector, limit=2
).points

print("\n🎯 Top Results:")
for i, result in enumerate(search_results):
    print(f"  {i + 1}. Score: {result.score:.4f} | Text: '{result.payload['text']}'")

print("\n🎉 Embedding and retrieval test completed successfully!")
