import pdfplumber

pdf_path = "documents/quest uni info.pdf"

with pdfplumber.open(pdf_path) as pdf:
    print("Total pages:", len(pdf.pages))

    for page_number, page in enumerate(pdf.pages, start=1):
        text = page.extract_text()

        print("\n" + "=" * 50)
        print("PAGE", page_number)
        print("=" * 50)

        if text:
            print(text[:1000])
        else:
            print("No text found on this page.")