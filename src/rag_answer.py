import os
import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Load API key
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Load embedding model
print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to ChromaDB
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection(name="quest_documents")

# Gemini
model = genai.GenerativeModel("gemini-3.6-flash")

# Ask question
question = input("\nAsk your question: ")

# Create question embedding
question_embedding = embedding_model.encode(question).tolist()

# Search database
results = collection.query(
    query_embeddings=[question_embedding],
    n_results=2
)

documents = results["documents"][0]
metadatas = results["metadatas"][0]

# Prepare context
context_parts = []

for document, metadata in zip(documents, metadatas):
    page = metadata["page"]

    context_parts.append(
        f"[PAGE {page}]\n{document}"
    )

context = "\n\n".join(context_parts)

# Prompt Gemini
prompt = f"""
You are a Smart Enquiry Assistant for QUEST University.

Answer the student's question ONLY using the university information below.

If the answer is not available, say:
"I could not find this information in the available university documents."

Do not make up information.

Student Question:
{question}

University Information:
{context}

Give a short and clear answer.
"""

print("\nGenerating answer...")

response = model.generate_content(prompt)

print("\n===== ANSWER =====")
print(response.text)

print("\n===== SOURCES =====")

shown_pages = []

for metadata in metadatas:
    page = metadata["page"]

    if page not in shown_pages:
        print(f"📄 QUEST University PDF - Page {page}")
        shown_pages.append(page)