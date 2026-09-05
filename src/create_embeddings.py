from sentence_transformers import SentenceTransformer

input_path = "data/chunks.txt"
output_path = "data/embeddings.txt"

print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

with open(input_path, "r", encoding="utf-8") as file:
    text = file.read()

chunks = text.split("===== CHUNK ")[1:]

print("Total chunks:", len(chunks))
print("Creating embeddings...")

with open(output_path, "w", encoding="utf-8") as file:

    for i, chunk in enumerate(chunks, start=1):
        embedding = model.encode(chunk)

        file.write(f"===== EMBEDDING {i} =====\n")
        file.write(",".join(map(str, embedding)))
        file.write("\n\n")

print("Embeddings created successfully!")
print("Saved to:", output_path)