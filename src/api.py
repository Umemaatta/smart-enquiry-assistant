"""
FastAPI backend for the Smart Enquiry Assistant.

This exposes the exact same retrieval + answer logic used by the Gradio
app (src/app.py) over a simple HTTP API, so the React frontend can call it.

No RAG logic is changed here: same ChromaDB collection, same BM25 index,
same SentenceTransformer embedding model, same Gemini prompt/rules,
same top-3 semantic + top-3 keyword retrieval and merge.

Run from the project root with:
    uvicorn src.api:app --reload --port 8000
"""

import os
import sys
import subprocess

import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi


# =========================================================
# 1. ENVIRONMENT
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Please add it to the environment variables."
    )

genai.configure(api_key=api_key)


# =========================================================
# 2. EMBEDDING MODEL
# =========================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# =========================================================
# 3. CHROMADB
# =========================================================

database_path = "data/chroma_db"

os.makedirs("data", exist_ok=True)

# data/chroma_db is gitignored, so a fresh deployment (Railway) starts with no
# vector database. data/quest_text.txt IS committed, so create_database.py can
# rebuild the collection from it on first boot. Without this the server would
# crash on startup with "collection quest_documents does not exist".
if not os.path.exists(database_path):

    print("ChromaDB not found. Building it from data/quest_text.txt ...")

    subprocess.run([sys.executable, "src/create_database.py"], check=True)

client = chromadb.PersistentClient(path=database_path)

try:

    collection = client.get_collection(name="quest_documents")

except Exception:

    print("Collection not found. Building the database ...")

    subprocess.run([sys.executable, "src/create_database.py"], check=True)

    collection = client.get_collection(name="quest_documents")

data = collection.get()

documents = data["documents"]
metadatas = data["metadatas"]


# =========================================================
# 4. BM25 SEARCH
# =========================================================

tokenized_documents = [document.lower().split() for document in documents]

bm25 = BM25Okapi(tokenized_documents)


# =========================================================
# 5. GEMINI
# =========================================================

model = genai.GenerativeModel("gemini-flash-lite-latest")


# =========================================================
# 6. RETRIEVAL + ANSWER (same logic as src/app.py)
# =========================================================

def get_answer(question: str) -> dict:

    question = question.strip()

    # -----------------------------------------------------
    # Semantic Search
    # -----------------------------------------------------

    question_embedding = embedding_model.encode(question).tolist()

    semantic_results = collection.query(
        query_embeddings=[question_embedding],
        n_results=3
    )

    semantic_documents = semantic_results["documents"][0]

    # -----------------------------------------------------
    # Keyword Search
    # -----------------------------------------------------

    tokenized_question = question.lower().split()

    bm25_scores = bm25.get_scores(tokenized_question)

    top_indexes = bm25_scores.argsort()[-3:][::-1]

    keyword_documents = [documents[index] for index in top_indexes]

    # -----------------------------------------------------
    # Combine Results
    # -----------------------------------------------------

    combined = []

    for document in (semantic_documents + keyword_documents):

        if document not in combined:

            combined.append(document)

    combined = combined[:3]

    # -----------------------------------------------------
    # Create Context
    # -----------------------------------------------------

    context_parts = []

    for document in combined:

        index = documents.index(document)

        page = metadatas[index]["page"]

        context_parts.append(f"[PAGE {page}]\n{document}")

    context = "\n\n".join(context_parts)

    # =====================================================
    # GEMINI PROMPT
    # =====================================================

    prompt = f"""

You are the Smart Enquiry Assistant for
Quaid-e-Awam University of Engineering,
Science & Technology, Nawabshah (QUEST).

Answer the student's question ONLY using the
university information provided below.

IMPORTANT RULES:

1. Do not use outside knowledge.
2. Do not make up information.
3. If the answer is not available, say exactly:

"I could not find this information in the available university documents."

4. Keep the answer short and clear.
5. Correct misleading questions using the available information.
6. Do not mention that you are an AI model.
7. Do not invent fees, dates, requirements or policies.
8. If the student asks in Roman Urdu, answer in simple Roman Urdu.

Student Question:
{question}

University Information:
{context}

"""

    try:

        response = model.generate_content(prompt)

        answer_text = response.text

    except Exception as error:

        print("Gemini Error:", error)

        answer_text = (
            "Sorry, I am unable to generate an answer "
            "right now. Please try again."
        )

    # =====================================================
    # SOURCES
    # =====================================================

    sources = []

    seen_pages = set()

    for document in combined:

        index = documents.index(document)

        page = metadatas[index]["page"]

        if page not in seen_pages:

            seen_pages.add(page)

            sources.append({
                "document": "QUEST University PDF",
                "page": page
            })

    return {
        "answer": answer_text,
        "sources": sources
    }


# =========================================================
# 7. FASTAPI APP
# =========================================================

app = FastAPI(title="Smart Enquiry Assistant API")

# Allow the React dev server (and any origin, for simplicity while
# learning/building). Tighten allow_origins before sharing this API
# publicly on its own.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Smart Enquiry Assistant API is running."}


@app.post("/ask")
def ask(request: AskRequest):

    if not request.question or not request.question.strip():
        return {"answer": "Please type a question.", "sources": []}

    return get_answer(request.question)


# =========================================================
# 8. REACT FRONTEND (production)
# =========================================================
#
# Serves the built React app (frontend/dist) from the same server, so the
# frontend and API share one origin and one URL. This mount must stay LAST:
# a mount on "/" would otherwise swallow the API routes above.
#
# In local development you normally run `npm run dev` instead, and this
# block is simply skipped when frontend/dist has not been built yet.

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

frontend_dist = os.path.join(PROJECT_ROOT, "frontend", "dist")

if os.path.isdir(frontend_dist):

    app.mount(
        "/",
        StaticFiles(directory=frontend_dist, html=True),
        name="frontend",
    )

    print(f"Serving React frontend from {frontend_dist}")

else:

    print("frontend/dist not found - API only (run 'npm run build' to serve the UI)")
