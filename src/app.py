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
    "gemini-3.6-flash"
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

        return history or [], ""

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

        sources = "\n".join(

            [

                f"📄 QUEST University PDF — Page {page}"

                for page in source_pages

            ]

        )

    else:

        sources = "No document source found."


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


    return history, sources


# =========================================================
# 9. CLEAR CHAT
# =========================================================

def clear_chat():

    return [], ""


# =========================================================
# 10. CSS
# =========================================================

css = """

body {
    background: #f4f7f9;
}

.gradio-container {
    max-width: 1150px !important;
}


/* =====================================================
   LARGE QUEST HEADER
   ===================================================== */

.quest-header {

    width: 100%;

    height: 380px;

    background: white;

    border-bottom: 5px solid #1f4e79;

    display: flex;

    justify-content: center;

    align-items: center;

    padding: 0;

    margin-bottom: 25px;

    box-shadow: 0 3px 12px rgba(0,0,0,0.08);

    box-sizing: border-box;
}


.quest-logo {

    display: block;

    width: 100%;

    height: 360px;

    object-fit: contain;

    object-position: center;
}


/* =====================================================
   PAGE TITLE
   ===================================================== */

.page-title {

    text-align: center;

    margin: 15px 0 30px 0;
}


.page-title h1 {

    color: #1f4e79;

    font-size: 32px;

    font-weight: 700;

    margin-bottom: 8px;
}


.page-title p {

    color: #666;

    font-size: 15px;

    margin-top: 0;
}


/* =====================================================
   ASK CARD
   ===================================================== */

.ask-card {

    background: white;

    padding: 20px;

    border-radius: 8px;

    border: 1px solid #dce2e7;

    box-shadow:
        0 2px 8px rgba(0,0,0,0.05);

    margin-bottom: 10px;
}


.ask-title {

    color: #1f4e79;

    font-size: 19px;

    font-weight: 700;
}


/* =====================================================
   QUESTION BOX
   ===================================================== */

#question-box textarea {

    border: 1px solid #cbd5df !important;

    border-radius: 6px !important;

    background: white !important;

    font-size: 15px !important;
}


#question-box textarea:focus {

    border: 2px solid #1f4e79 !important;
}


/* =====================================================
   BUTTON
   ===================================================== */

#ask-button {

    background: #1f4e79 !important;

    color: white !important;

    border: none !important;

    font-weight: 600 !important;
}


#ask-button:hover {

    background: #163b5d !important;
}


/* =====================================================
   CONVERSATION
   ===================================================== */

.conversation-title {

    color: #1f4e79;

    font-size: 19px;

    font-weight: 700;

    margin-bottom: 8px;
}


.chat-container {

    background: white;

    border: 1px solid #dce2e7;

    border-radius: 8px;

    box-shadow:
        0 2px 8px rgba(0,0,0,0.05);
}


/* =====================================================
   SOURCES
   ===================================================== */

.sources-title {

    color: #1f4e79;

    font-size: 18px;

    font-weight: 700;
}


#source-box textarea {

    background: white !important;
}


/* =====================================================
   COMMON QUESTIONS
   ===================================================== */

.common-title {

    color: #1f4e79;

    font-size: 19px;

    font-weight: 700;

    margin-top: 25px;
}


.question-card {

    background: white;

    border: 1px solid #dce2e7;

    border-radius: 6px;

    padding: 12px 15px;

    margin: 6px 0;

    color: #444;
}


/* =====================================================
   FOOTER
   ===================================================== */

.quest-footer {

    text-align: center;

    background: white;

    border-top: 3px solid #1f4e79;

    padding: 22px 15px;

    margin-top: 30px;

    color: #666;

    font-size: 13px;

    line-height: 1.7;
}


.footer-title {

    color: #1f4e79;

    font-weight: 700;

    font-size: 14px;
}


/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 700px) {

    .quest-header {

        min-height: 220px;

        height: 220px;

        padding: 5px 10px;
    }


    .quest-logo {

        width: 330px;

        height: 210px;
    }


    .page-title h1 {

        font-size: 25px;
    }

}

"""


# =========================================================
# 11. GRADIO APP
# =========================================================

with gr.Blocks(
    title="QUEST Smart Enquiry Assistant"
) as app:


    # -----------------------------------------------------
    # HEADER - ONLY QUEST LOGO
    # -----------------------------------------------------

    gr.HTML(

        f"""

        <div class="quest-header">

            <img
                src="data:image/png;base64,{logo_base64}"
                class="quest-logo"
                alt="QUEST Logo"
            >

        </div>

        """

    )


    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    gr.HTML(

        """

        <div class="page-title">

            <h1>
                Smart Enquiry Assistant
            </h1>

            <p>
                Get quick answers about admissions,
                eligibility, fees and university procedures.
            </p>

        </div>

        """

    )


    # -----------------------------------------------------
    # ASK QUESTION
    # -----------------------------------------------------

    gr.HTML(

        """

        <div class="ask-card">

            <div class="ask-title">
                🔎 Ask Your Question
            </div>

        </div>

        """

    )


    question = gr.Textbox(

        label="Question",

        placeholder="Type your question here...",

        lines=2,

        elem_id="question-box"

    )


    # -----------------------------------------------------
    # BUTTONS
    # -----------------------------------------------------

    with gr.Row():

        ask_button = gr.Button(

            "Ask Question",

            variant="primary",

            elem_id="ask-button"

        )


        clear_button = gr.Button(

            "Clear Conversation"

        )


    # -----------------------------------------------------
    # CONVERSATION
    # -----------------------------------------------------

    gr.Markdown(

        "### 💬 Conversation",

        elem_classes=["conversation-title"]

    )


    chatbot = gr.Chatbot(

        label="",

        height=450,

        elem_classes=["chat-container"]

    )


    # -----------------------------------------------------
    # SOURCES
    # -----------------------------------------------------

    gr.Markdown(

        "### 📚 Document Sources",

        elem_classes=["sources-title"]

    )


    source = gr.Textbox(

        label="Retrieved information",

        interactive=False,

        lines=3,

        elem_id="source-box"

    )


    # -----------------------------------------------------
    # COMMON QUESTIONS
    # -----------------------------------------------------

    gr.Markdown(

        "### 💡 Common Questions",

        elem_classes=["common-title"]

    )


    gr.Markdown(

        """

        <div class="question-card">
        • What is the minimum percentage required for Engineering programs?
        </div>

        <div class="question-card">
        • How is the merit calculated?
        </div>

        <div class="question-card">
        • What is the fee for B.E programs?
        </div>

        <div class="question-card">
        • Is Pre-Medical eligible for Artificial Intelligence?
        </div>

        """

    )


    # -----------------------------------------------------
    # FOOTER
    # -----------------------------------------------------

    gr.HTML(

        """

        <div class="quest-footer">

            <div class="footer-title">
                Smart Enquiry Assistant
            </div>

            This system provides answers only from
            available university documents.

            <br>

            Please verify important information
            with QUEST University.

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
            chatbot,
            source
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
            chatbot,
            source
        ]

    ).then(

        fn=lambda: "",

        outputs=question

    )


    clear_button.click(

        fn=clear_chat,

        outputs=[
            chatbot,
            source
        ]

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