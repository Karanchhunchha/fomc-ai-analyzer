from pypdf import PdfReader

reader = PdfReader("data/raw/fomcminutes20260128.pdf")

text = ""

for page in reader.pages:
    extracted = page.extract_text()

    if extracted:
        text += extracted

# Save extracted text
with open("data/fomc_text.txt", "w", encoding="utf-8") as file:
    file.write(text)

print("Text extraction complete!")
print(text[:3000])