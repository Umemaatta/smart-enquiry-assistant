import os
import sys
import base64
import subprocess

import chromadb
import gradio as gr
import google.generativeai as genai

from dotenv import load_dotenv
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

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# =========================================================
# 3. CHROMADB
# =========================================================

database_path = "data/chroma_db"

os.makedirs("data", exist_ok=True)


# If ChromaDB does not exist, create it automatically
if not os.path.exists(database_path):

    print("ChromaDB not found.")
    print("Creating database from university PDF...")

    subprocess.run(
        [sys.executable, "src/create_database.py"],
        check=True
    )

    print("Database created successfully.")


client = chromadb.PersistentClient(
    path=database_path
)


try:

    collection = client.get_collection(
        name="quest_documents"
    )

except Exception:

    print("QUEST collection not found.")
    print("Creating database...")

    subprocess.run(
        [sys.executable, "src/create_database.py"],
        check=True
    )

    collection = client.get_collection(
        name="quest_documents"
    )


# =========================================================
# 4. DOCUMENTS
# =========================================================

data = collection.get()

documents = data["documents"]
metadatas = data["metadatas"]


# =========================================================
# 5. BM25 SEARCH
# =========================================================

tokenized_documents = [
    document.lower().split()
    for document in documents
]

bm25 = BM25Okapi(
    tokenized_documents
)


# =========================================================
# 6. GEMINI
# =========================================================

model = genai.GenerativeModel(
    "gemini-flash-lite-latest"
)


# =========================================================
# 7. QUEST LOGO
# =========================================================

logo_path = "assets/quest_logo.png"

if not os.path.exists(logo_path):

    raise FileNotFoundError(
        "QUEST logo not found. Please make sure this file exists:\n"
        "assets/quest_logo.png"
    )


with open(logo_path, "rb") as image_file:

    logo_base64 = base64.b64encode(
        image_file.read()
    ).decode("utf-8")


# =========================================================
# 8. ANSWER FUNCTION
# =========================================================

def answer_question(question, history):

    if not question or not question.strip():

        return history or []

    question = question.strip()


    # -----------------------------------------------------
    # Semantic Search
    # -----------------------------------------------------

    question_embedding = embedding_model.encode(
        question
    ).tolist()


    semantic_results = collection.query(

        query_embeddings=[
            question_embedding
        ],

        n_results=3
    )


    semantic_documents = semantic_results[
        "documents"
    ][0]


    # -----------------------------------------------------
    # Keyword Search
    # -----------------------------------------------------

    tokenized_question = question.lower().split()


    bm25_scores = bm25.get_scores(
        tokenized_question
    )


    top_indexes = bm25_scores.argsort()[-3:][::-1]


    keyword_documents = [

        documents[index]

        for index in top_indexes

    ]


    # -----------------------------------------------------
    # Combine Results
    # -----------------------------------------------------

    combined = []


    for document in (
        semantic_documents + keyword_documents
    ):

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


        context_parts.append(

            f"[PAGE {page}]\n{document}"

        )


    context = "\n\n".join(
        context_parts
    )


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


    print("\nGenerating answer...")


    try:

        response = model.generate_content(
            prompt
        )

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

    source_pages = []


    for document in combined:

        index = documents.index(document)

        page = metadatas[index]["page"]


        if page not in source_pages:

            source_pages.append(page)


    if source_pages:

        pages_line = " · ".join(f"Page {page}" for page in source_pages)

        answer_text = f"{answer_text}\n\n**Sources:** {pages_line}"

    else:

        answer_text = f"{answer_text}\n\n*No document source found for this answer.*"


    # =====================================================
    # CHAT HISTORY
    # =====================================================

    history = history or []


    history.append(

        {
            "role": "user",
            "content": question
        }

    )


    history.append(

        {
            "role": "assistant",
            "content": answer_text
        }

    )


    return history


# =========================================================
# 9. CLEAR CHAT
# =========================================================

def clear_chat():

    return []


# =========================================================
# 10. CSS
# =========================================================

css = """

:root {
    --quest-navy: #1f4e79;
    --quest-navy-dark: #163b5d;
    --quest-bg: #f4f6f9;
    --quest-border: #dde3ea;
    --quest-text: #2a2f36;
    --quest-muted: #667080;
}

body {
    background: var(--quest-bg);
}

.gradio-container {
    max-width: 880px !important;
}


/* =====================================================
   HERO (LOGO + TITLE)
   ===================================================== */

.quest-hero {

    width: 100%;

    display: flex;

    flex-direction: column;

    align-items: center;

    text-align: center;

    padding: 28px 16px 20px 16px;

    box-sizing: border-box;
}


.quest-logo {

    height: clamp(72px, 12vw, 150px);

    width: auto;

    max-width: 90vw;

    object-fit: contain;

    display: block;

    margin: 0 auto 14px auto;
}


.quest-hero h1 {

    color: var(--quest-navy);

    font-size: clamp(20px, 3vw, 28px);

    font-weight: 700;

    margin: 0 0 4px 0;

    line-height: 1.25;
}


.quest-hero .quest-subtitle {

    color: var(--quest-muted);

    font-size: 14px;

    font-weight: 500;

    margin: 0;
}


/* =====================================================
   CHAT SHELL (single cohesive panel)
   ===================================================== */

.chat-shell {

    background: #ffffff;

    border: 1px solid var(--quest-border);

    border-radius: 16px;

    box-shadow: 0 2px 14px rgba(20, 30, 45, 0.06);

    padding: 10px 18px 18px 18px;

    box-sizing: border-box;
}


.chat-toolbar {

    display: flex;

    justify-content: flex-end;

    padding: 6px 0 2px 0;
}


#clear-button {

    background: transparent !important;

    color: var(--quest-muted) !important;

    border: 1px solid var(--quest-border) !important;

    border-radius: 20px !important;

    font-weight: 500 !important;

    font-size: 12.5px !important;

    padding: 4px 14px !important;

    box-shadow: none !important;
}


#clear-button:hover {

    color: var(--quest-navy) !important;

    border-color: var(--quest-navy) !important;
}


/* =====================================================
   CHAT WINDOW
   ===================================================== */

.chat-window {

    background: #fbfcfd;

    border: 1px solid var(--quest-border) !important;

    border-radius: 12px;
}


.chat-window .message-wrap,
.chat-window .prose {

    font-size: 15.5px !important;

    line-height: 1.65 !important;
}


/* =====================================================
   INPUT ROW
   ===================================================== */

.input-row {

    margin-top: 12px;

    align-items: flex-end !important;

    gap: 8px;
}


#question-box textarea {

    border: 1px solid #cbd5df !important;

    border-radius: 22px !important;

    background: #fbfcfd !important;

    font-size: 15px !important;

    padding: 12px 18px !important;
}


#question-box textarea:focus {

    border: 2px solid var(--quest-navy) !important;
}


#ask-button {

    background: var(--quest-navy) !important;

    color: white !important;

    border: none !important;

    font-weight: 600 !important;

    border-radius: 22px !important;

    min-width: 84px;
}


#ask-button:hover {

    background: var(--quest-navy-dark) !important;
}


/* =====================================================
   EXAMPLE CHIPS
   ===================================================== */

.chip-label {

    margin-top: 16px !important;

    color: var(--quest-muted) !important;

    font-size: 13px !important;
}

.chip-label p {
    margin: 0 !important;
}


.chip-row {

    flex-wrap: wrap !important;

    gap: 8px !important;
}


.example-chip {

    background: #eef3f8 !important;

    color: var(--quest-navy) !important;

    border: 1px solid var(--quest-border) !important;

    border-radius: 18px !important;

    font-size: 13px !important;

    font-weight: 500 !important;

    padding: 7px 15px !important;

    box-shadow: none !important;

    width: auto !important;

    flex: 0 1 auto !important;
}


.example-chip:hover {

    background: var(--quest-navy) !important;

    color: white !important;

    border-color: var(--quest-navy) !important;
}


/* =====================================================
   FOOTER
   ===================================================== */

.quest-footer {

    text-align: center;

    padding: 16px 15px 4px 15px;

    color: var(--quest-muted);

    font-size: 12.5px;

    line-height: 1.6;
}


.quest-footer .footer-title {

    color: var(--quest-navy);

    font-weight: 700;
}


/* =====================================================
   RESPONSIVE
   ===================================================== */

@media (max-width: 1024px) {

    .gradio-container {

        max-width: 100% !important;

        padding: 0 16px !important;
    }
}


@media (max-width: 700px) {

    .quest-hero {

        padding: 18px 8px 14px 8px;
    }

    .chat-shell {

        padding: 8px 10px 12px 10px;

        border-radius: 12px;
    }

    #question-box textarea {

        padding: 10px 14px !important;
    }

    .example-chip {

        font-size: 12.5px !important;

        padding: 6px 12px !important;
    }
}

"""


# =========================================================
# 11. GRADIO APP
# =========================================================

EXAMPLE_QUESTIONS = [
    "What is the minimum percentage required for Engineering programs?",
    "How is the merit calculated?",
    "What is the fee for B.E programs?",
    "Is Pre-Medical eligible for Artificial Intelligence?",
]

with gr.Blocks(
    title="QUEST Smart Enquiry Assistant",
) as app:


    # -----------------------------------------------------
    # HERO (LOGO + TITLE)
    # -----------------------------------------------------

    gr.HTML(

        f"""

        <div class="quest-hero">

            <img
                src="data:image/png;base64,{logo_base64}"
                class="quest-logo"
                alt="QUEST Logo"
            >

            <h1>Smart Enquiry Assistant</h1>
            <p class="quest-subtitle">Your AI-powered university information assistant</p>

        </div>

        """

    )


    # -----------------------------------------------------
    # CHAT SHELL
    # -----------------------------------------------------

    with gr.Column(elem_classes=["chat-shell"]):

        with gr.Row(elem_classes=["chat-toolbar"]):

            clear_button = gr.Button(
                "Clear Chat",
                elem_id="clear-button",
                size="sm",
            )

        chatbot = gr.Chatbot(

            label="",

            height=480,

            elem_classes=["chat-window"],

            placeholder="Ask a question about QUEST University to get started.",

        )

        with gr.Row(elem_classes=["input-row"]):

            question = gr.Textbox(

                label="",

                show_label=False,

                placeholder="Ask anything about QUEST University...",

                lines=1,

                max_lines=6,

                elem_id="question-box",

                scale=8,

            )

            ask_button = gr.Button(

                "Ask",

                variant="primary",

                elem_id="ask-button",

                scale=1,

            )

        gr.Markdown("**Try asking**", elem_classes=["chip-label"])

        with gr.Row(elem_classes=["chip-row"]):

            example_buttons = [
                gr.Button(q, elem_classes=["example-chip"])
                for q in EXAMPLE_QUESTIONS
            ]


    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    gr.HTML(

        """

        <div class="quest-footer">

            <div class="footer-title">Smart Enquiry Assistant | University Information System</div>

            This system provides answers only from available university documents.
            Please verify important information with QUEST University.

        </div>

        """

    )


    # =====================================================
    # EVENTS
    # =====================================================

    ask_button.click(

        fn=answer_question,

        inputs=[
            question,
            chatbot
        ],

        outputs=[
            chatbot
        ]

    ).then(

        fn=lambda: "",

        outputs=question

    )


    question.submit(

        fn=answer_question,

        inputs=[
            question,
            chatbot
        ],

        outputs=[
            chatbot
        ]

    ).then(

        fn=lambda: "",

        outputs=question

    )


    clear_button.click(

        fn=clear_chat,

        outputs=[
            chatbot
        ]

    )


    for btn, example_text in zip(example_buttons, EXAMPLE_QUESTIONS):

        btn.click(

            fn=lambda example_text=example_text: example_text,

            outputs=[question]

        ).then(

            fn=answer_question,

            inputs=[question, chatbot],

            outputs=[chatbot]

        ).then(

            fn=lambda: "",

            outputs=question

        )


# =========================================================
# 12. RUN APP
# =========================================================

app.launch(

    theme=gr.themes.Soft(),

    css=css,

    server_name="0.0.0.0",

    server_port=int(
        os.environ.get("PORT", 7860)
    )

)
