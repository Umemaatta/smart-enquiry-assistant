import os, json, re, csv, time
import chromadb
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY was not found. Keep your API key in your local .env file.")

genai.configure(api_key=api_key)
print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection(name="quest_documents")
data = collection.get()
documents = data["documents"]
metadatas = data["metadatas"]
bm25 = BM25Okapi([d.lower().split() for d in documents])
model = genai.GenerativeModel("gemini-flash-lite-latest")

with open("evaluation/questions.json", encoding="utf-8") as f:
    questions = json.load(f)

REFUSAL = "I could not find this information in the available university documents."

def retrieve(question):
    emb = embedding_model.encode(question).tolist()
    semantic = collection.query(query_embeddings=[emb], n_results=3)["documents"][0]
    scores = bm25.get_scores(question.lower().split())
    indexes = scores.argsort()[-3:][::-1]
    keyword = [documents[i] for i in indexes]
    combined = []
    for d in semantic + keyword:
        if d not in combined:
            combined.append(d)
    combined = combined[:3]
    parts, pages = [], []
    for d in combined:
        i = documents.index(d)
        page = metadatas[i]["page"]
        pages.append(page)
        parts.append(f"[PAGE {page}]\n{d}")
    return "\n\n".join(parts), sorted(set(pages))

def ask(question, context):
    prompt = f"""You are a Smart Enquiry Assistant for QUEST University.
Answer using ONLY the university information provided below.

Rules:
1. Do not use outside knowledge.
2. Do not make up information.
3. If the information is not available in the provided context, say exactly:
"{REFUSAL}"
4. Keep the answer short and clear.
5. If the context contains the answer, answer directly.
6. Do not mention that you are an AI model.

Student Question:
{question}

University Information:
{context}
"""
    for attempt in range(5):
        try:
            return model.generate_content(prompt).text.strip()
        except ResourceExhausted:
            if attempt == 4:
                raise
            time.sleep(15)

def keyword_pass(answer, keywords):
    a = re.sub(r"\s+", " ", answer.lower())
    return all(k.lower() in a for k in keywords)

results = []
for n, item in enumerate(questions, 1):
    print(f"[{n}/100] {item['question']}")
    try:
        context, retrieved_pages = retrieve(item["question"])
        answer = ask(item["question"], context)

        if item["answerable"]:
            correct = keyword_pass(answer, item["keywords"])
            refusal = None
            ref_pages = {str(p) for p in item["reference_pages"]}
            got_pages = {str(p) for p in retrieved_pages}
            page_hit = bool(ref_pages & got_pages)
        else:
            correct = REFUSAL.lower() in answer.lower()
            refusal = correct
            page_hit = None

        results.append({
            "id": item["id"],
            "question": item["question"],
            "answerable": item["answerable"],
            "reference_answer": item["reference_answer"],
            "ai_answer": answer,
            "reference_pages": item["reference_pages"],
            "retrieved_pages": retrieved_pages,
            "answer_correct": correct,
            "page_retrieval_hit": page_hit,
            "refusal_correct": refusal
        })
        time.sleep(0.3)
    except Exception as e:
        results.append({
            "id": item["id"], "question": item["question"],
            "answerable": item["answerable"],
            "reference_answer": item["reference_answer"], "ai_answer": "",
            "reference_pages": item["reference_pages"], "retrieved_pages": [],
            "answer_correct": False,
            "page_retrieval_hit": False if item["answerable"] else None,
            "refusal_correct": False if not item["answerable"] else None,
            "error": str(e)
        })

def percentage(values):
    vals = [v for v in values if v is not None]
    return round(100 * sum(bool(v) for v in vals) / len(vals), 2) if vals else 0.0

summary = {
    "total_questions": 100,
    "answerable_questions": sum(r["answerable"] for r in results),
    "unanswerable_questions": sum(not r["answerable"] for r in results),
    "overall_answer_accuracy_percent": percentage([r["answer_correct"] for r in results]),
    "answerable_page_retrieval_hit_percent": percentage([r["page_retrieval_hit"] for r in results if r["answerable"]]),
    "unanswerable_refusal_accuracy_percent": percentage([r["refusal_correct"] for r in results if not r["answerable"]])
}

os.makedirs("evaluation/results", exist_ok=True)
with open("evaluation/results/results.json", "w", encoding="utf-8") as f:
    json.dump({"summary": summary, "results": results}, f, indent=2, ensure_ascii=False)

with open("evaluation/results/results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id","question","answerable","reference_answer","ai_answer",
                "reference_pages","retrieved_pages","answer_correct",
                "page_retrieval_hit","refusal_correct"])
    for r in results:
        w.writerow([
            r["id"], r["question"], r["answerable"], r["reference_answer"],
            r["ai_answer"], ",".join(map(str,r["reference_pages"])),
            ",".join(map(str,r["retrieved_pages"])), r["answer_correct"],
            r["page_retrieval_hit"], r["refusal_correct"]
        ])

print("\n===== EVALUATION SUMMARY =====")
for k, v in summary.items():
    print(f"{k}: {v}")
print("\nResults saved in evaluation/results/")
