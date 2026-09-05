import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# Load embedding model
print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to ChromaDB
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection(name="quest_documents")

# Get all documents
data = collection.get()

documents = data["documents"]

# Create BM25 index
tokenized_documents = [
    document.lower().split()
    for document in documents
]

bm25 = BM25Okapi(tokenized_documents)

# Ask question
question = input("\nAsk your question: ")

# Semantic search
question_embedding = embedding_model.encode(question).tolist()

semantic_results = collection.query(
    query_embeddings=[question_embedding],
    n_results=3
)

semantic_documents = semantic_results["documents"][0]

# Keyword search
tokenized_question = question.lower().split()

bm25_scores = bm25.get_scores(tokenized_question)

top_indexes = bm25_scores.argsort()[-3:][::-1]

keyword_documents = [
    documents[index]
    for index in top_indexes
]

# Combine results
combined_documents = []

for document in semantic_documents + keyword_documents:
    if document not in combined_documents:
        combined_documents.append(document)

print("\n===== HYBRID SEARCH RESULTS =====")

for i, document in enumerate(combined_documents[:3], start=1):
    print(f"\n--- Result {i} ---")
    print(document[:1000])