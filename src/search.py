import chromadb
from sentence_transformers import SentenceTransformer

print("Loading model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="data/chroma_db")

collection = client.get_collection(
    name="quest_documents"
)

question = input("Ask your question: ")

question_embedding = model.encode(question).tolist()

results = collection.query(
    query_embeddings=[question_embedding],
    n_results=2
)

print("\n===== RELEVANT INFORMATION =====")

for i, document in enumerate(results["documents"][0], start=1):
    print(f"\n--- Result {i} ---")
    print(document[:1500])