input_path = "data/quest_text.txt"
output_path = "data/chunks.txt"

with open(input_path, "r", encoding="utf-8") as file:
    text = file.read()

# Text ko approximately 1000 characters ke chunks mein divide karna
chunk_size = 1000
overlap = 200

chunks = []

start = 0

while start < len(text):
    end = start + chunk_size
    chunk = text[start:end]

    chunks.append(chunk)

    start = end - overlap

with open(output_path, "w", encoding="utf-8") as file:
    for i, chunk in enumerate(chunks, start=1):
        file.write(f"\n\n===== CHUNK {i} =====\n\n")
        file.write(chunk)

print("Text successfully divided into chunks!")
print("Total chunks:", len(chunks))
print("Saved to:", output_path)