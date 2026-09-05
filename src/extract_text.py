import pdfplumber

pdf_path = "documents/quest uni info.pdf"
output_path = "data/quest_text.txt"

with pdfplumber.open(pdf_path) as pdf:
    with open(output_path, "w", encoding="utf-8") as file:

        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()

            file.write(f"\n\n===== PAGE {page_number} =====\n\n")

            if text:
                file.write(text)
            else:
                file.write("No text found on this page.")

print("PDF text successfully extracted!")
print("Saved to:", output_path)