import os
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# -----------------------------
# 1. Load API key
# -----------------------------
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# -----------------------------
# 2. Load embedding model
# -----------------------------
print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------
# 3. Connect to ChromaDB
# -----------------------------
client = chromadb.PersistentClient(path="data/chroma_db")

collection = client.get_collection(
    name="quest_documents"
)

# -----------------------------
# 4. Get all documents
# -----------------------------
data = collection.get()

documents = data["documents"]
metadatas = data["metadatas"]

# -----------------------------
# 5. Create BM25 index
# -----------------------------
tokenized_documents = [
    document.lower().split()
    for document in documents
]

bm25 = BM25Okapi(tokenized_documents)

# -----------------------------
# 6. Ask question
# -----------------------------
question = input("\nAsk your question: ")

# -----------------------------
# 7. Semantic search
# -----------------------------
question_embedding = embedding_model.encode(question).tolist()

semantic_results = collection.query(
    query_embeddings=[question_embedding],
    n_results=3
)

semantic_documents = semantic_results["documents"][0]

# -----------------------------
# 8. Keyword search
# -----------------------------
tokenized_question = question.lower().split()

bm25_scores = bm25.get_scores(tokenized_question)

top_indexes = bm25_scores.argsort()[-3:][::-1]

keyword_documents = [
    documents[index]
    for index in top_indexes
]

# -----------------------------
# 9. Combine results
# -----------------------------
combined = []

for document in semantic_documents + keyword_documents:

    if document not in combined:
        combined.append(document)

combined = combined[:3]

# -----------------------------
# 10. Create context
# -----------------------------
context_parts = []

for document in combined:

    # Find matching metadata
    index = documents.index(document)

    page = metadatas[index]["page"]

    context_parts.append(
        f"[PAGE {page}]\n{document}"
    )

context = "\n\n".join(context_parts)

# -----------------------------
# 11. Gemini
# -----------------------------
model = genai.GenerativeModel(
    "gemini-3.6-flash"
)

prompt = f"""
You are a Smart Enquiry Assistant for QUEST University.

Your job is to answer student questions using ONLY the university
information provided below.

IMPORTANT RULES:

1. Do not use outside knowledge.
2. Do not make up information.
3. If the information is not available in the provided context,
   say exactly:

"I could not find this information in the available university documents."

4. Keep the answer short and clear.
5. If the context contains the answer, answer directly.
6. Do not mention that you are an AI model.

Student Question:
{question}

University Information:
{context}
"""

print("\nGenerating answer...")

response = model.generate_content(prompt)

# -----------------------------
# 12. Final answer
# -----------------------------
print("\n===== ANSWER =====")
print(response.text)

# -----------------------------
# 13. Sources
# -----------------------------
print("\n===== SOURCES =====")

shown_pages = []

for document in combined:

    index = documents.index(document)

    page = metadatas[index]["page"]

    if page not in shown_pages:

        print(f"📄 QUEST University PDF - Page {page}")

        shown_pages.append(page)