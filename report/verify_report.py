"""Validate the finished DOCX and the Word-rendered six-page PDF."""
import csv
from pathlib import Path
import re
from docx import Document
from docx.oxml.ns import qn
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / "report"
doc = Document(folder / "DNA_Motif_Finder_Report.docx")
body = "\n".join(p.text for p in doc.paragraphs)
cells = "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
assert "Har Agam Deep Singh" in body and "03714802724" in body
assert len(doc.inline_shapes) == 6
assert len(doc.tables) == 7
for section in doc.sections:
    assert not any(p.text.strip() for p in section.header.paragraphs)
    assert not any(p.text.strip() for p in section.footer.paragraphs)
assert "MAHARAJA AGRASEN" not in body
assert doc.styles["Normal"].font.name == "Calibri"
assert doc.styles["Normal"].font.size.pt == 10
for name in ("Title", "Subtitle", "Heading 1", "Heading 2", "Caption"):
    assert doc.styles[name].font.name == "Calibri"
    assert doc.styles[name].font.size.pt in (9.5, 10)
for run in doc.element.iter(qn("w:r")):
    if run.find(qn("w:t")) is None:
        continue
    rp = run.find(qn("w:rPr"))
    assert rp is not None
    fonts = rp.find(qn("w:rFonts"))
    assert fonts is not None and fonts.get(qn("w:ascii")) == "Calibri"
    size = rp.find(qn("w:sz"))
    if size is not None:
        assert size.get(qn("w:val")) in ("19", "20")
assert abs(doc.sections[0].page_width.mm - 210) < .1
assert abs(doc.sections[0].page_height.mm - 297) < .1
available = doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin
for table in doc.tables:
    for row in table.rows:
        assert sum(c.width for c in row.cells) <= available

with (ROOT / "results/chart_scaling.csv").open(newline="", encoding="utf-8") as f:
    scaling = list(csv.DictReader(f))
for row in scaling:
    assert f"{float(row['time_ms']):.4f}" in cells
    if int(row["n"]) == 100000:
        assert f"{int(row['comparisons']):,}" in cells
with (ROOT / "results/chart_collisions.csv").open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        for key in ("spurious_hits", "min_spurious_hits", "max_spurious_hits"):
            assert f"{int(row[key]):,}" in cells
assert not re.search(r"\[(?:STUDENT|ENROLLMENT|FINAL|MEASURED|FIGURE)_[A-Z_]+\]", body + cells)
for term in ("BUILD_LPS", "KMP(T, P)", "RABIN_KARP(T, P, q)",
             "Correctness", "References", "525", "O(n+m)", "O(nm)"):
    assert term in body
pdf = PdfReader(folder / "DNA_Motif_Finder_Report.pdf")
assert len(pdf.pages) == 6
page_heads = ("1. Abstract", "4. Knuth", "5. Rabin", "6. Implementation", "8. Character", "9. Correctness")
for page, heading in zip(pdf.pages, page_heads):
    text = page.extract_text()
    assert heading in text, (heading, text[:200])
    assert len(text.split()) > 200
    assert abs(float(page.mediabox.width) - 595.28) < 1
    assert abs(float(page.mediabox.height) - 841.89) < 1
# Bounding boxes catch text clipping beyond the physical page; visual review
# additionally checks table fills, diagrams, spacing, and readable chart labels.
rendered = pdfium.PdfDocument(folder / "DNA_Motif_Finder_Report.pdf")
for i in range(len(rendered)):
    page = rendered[i]
    textpage = page.get_textpage()
    width, height = page.get_size()
    for j in range(textpage.count_chars()):
        if not textpage.get_text_range(j, 1).strip():
            continue
        left, bottom, right, top = textpage.get_charbox(j)
        assert 0 <= left <= right <= width, (i, j, left, right)
        assert 0 <= bottom <= top <= height, (i, j, bottom, top)
    textpage.close(); page.close()
rendered.close()
print("REPORT VERIFIED: six A4 pages, Calibri 10/9.5, seven tables, six visuals, clear title block, empty headers/footers, measured values checked")
