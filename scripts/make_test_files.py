"""
Generate synthetic test files in data/sample_documents/.

Run once:  python scripts/make_test_files.py
NEVER put real personal information in this project's test data.
"""
from pathlib import Path

import fitz
from docx import Document

OUT = Path(__file__).resolve().parent.parent / "data" / "sample_documents"
OUT.mkdir(parents=True, exist_ok=True)

# ---- A small fake business letter as TXT -----------------------------
TXT_BODY = """ACME Corporation — Employment Verification

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
(OUT / "sample_letter.txt").write_text(TXT_BODY, encoding="utf-8")

# ---- Same letter as DOCX ---------------------------------------------
doc = Document()
doc.add_heading("ACME Corporation — Employment Verification", level=1)
for line in TXT_BODY.splitlines():
    doc.add_paragraph(line)
doc.add_heading("Table of recent contacts", level=2)
table = doc.add_table(rows=2, cols=2)
table.rows[0].cells[0].text = "Name"
table.rows[0].cells[1].text = "Email"
table.rows[1].cells[0].text = "Bob Sample"
table.rows[1].cells[1].text = "bob.sample@example.com"
doc.save(str(OUT / "sample_letter.docx"))

# ---- Same letter as PDF ----------------------------------------------
pdf = fitz.open()
page = pdf.new_page()
page.insert_text(
    (72, 72),
    TXT_BODY,
    fontsize=11,
    fontname="helv",
    wrap_text=True,
)
pdf.save(str(OUT / "sample_letter.pdf"))
pdf.close()

print(f"Wrote test files to {OUT}")