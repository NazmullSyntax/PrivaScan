"""Generate synthetic test files in data/sample_documents/."""
from pathlib import Path
import fitz
from docx import Document

OUT = Path(__file__).resolve().parent.parent / "data" / "sample_documents"
OUT.mkdir(parents=True, exist_ok=True)

TXT_BODY = """ACME Corporation - Employment Verification

Employee: Alice Testerson
Email: alice.testerson@example.com
Phone: +1-555-010-2030
SSN (sample format): 123-45-6789
Passport (sample format): AB1234567
Bank account: 1234567890123
Address: 742 Evergreen Avenue

Alice has been with the company since 2020 and works as a Data Analyst.
This is synthetic data used only for testing.
"""

# TXT
(OUT / "sample_letter.txt").write_text(TXT_BODY, encoding="utf-8")

# DOCX
doc = Document()
doc.add_heading("ACME Corporation - Employment Verification", level=1)
for line in TXT_BODY.splitlines():
    doc.add_paragraph(line)
doc.add_heading("Table of recent contacts", level=2)
table = doc.add_table(rows=2, cols=2)
table.rows[0].cells[0].text = "Name"
table.rows[0].cells[1].text = "Email"
table.rows[1].cells[0].text = "Bob Sample"
table.rows[1].cells[1].text = "bob.sample@example.com"
doc.save(str(OUT / "sample_letter.docx"))

# PDF — manual line wrapping (PyMuPDF 1.24.2 has no wrap_text param)
pdf = fitz.open()
page = pdf.new_page()
y = 72
for line in TXT_BODY.splitlines():
    page.insert_text((72, y), line, fontsize=11, fontname="helv")
    y += 14
pdf.save(str(OUT / "sample_letter.pdf"))
pdf.close()

print(f"Wrote 3 files to: {OUT}")
for f in sorted(OUT.glob("sample_letter.*")):
    print(f"  - {f.name} ({f.stat().st_size} bytes)")
