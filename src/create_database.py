import chromadb
from sentence_transformers import SentenceTransformer

print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Reading PDF text...")

with open("data/quest_text.txt", "r", encoding="utf-8") as file:
    text = file.read()

# Split PDF into pages
pages = text.split("===== PAGE ")

documents = []
metadatas = []
ids = []

chunk_id = 1

for page in pages[1:]:

    lines = page.split("\n")

    page_number = lines[0].replace("=====", "").strip()

    page_text = "\n".join(lines[1:]).strip()

    # Split page text into smaller chunks
    chunk_size = 1000
    overlap = 200

    start = 0

    while start < len(page_text):

        end = start + chunk_size
        chunk = page_text[start:end]

        if chunk.strip():
            documents.append(chunk)
            metadatas.append({
                "page": page_number
            })
            ids.append(str(chunk_id))

            chunk_id += 1

        start = end - overlap

print("Total chunks:", len(documents))

print("Creating ChromaDB...")

client = chromadb.PersistentClient(path="data/chroma_db")

# Delete old collection
try:
    client.delete_collection("quest_documents")
except:
    pass

collection = client.create_collection(
    name="quest_documents"
)

print("Creating embeddings...")

embeddings = model.encode(documents).tolist()

collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas
)

print("Database created successfully!")
print("Total documents stored:", collection.count())