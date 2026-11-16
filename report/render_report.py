"""Export through an isolated, invisible Microsoft Word instance."""
from pathlib import Path
import json
import win32com.client
from pypdf import PdfReader
import pypdfium2 as pdfium

folder = Path(__file__).resolve().parent
source = folder / "DNA_Motif_Finder_Report.docx"
target = folder / "DNA_Motif_Finder_Report.pdf"
word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
document = None
try:
    document = word.Documents.Open(str(source), ReadOnly=False, AddToRecentFiles=False)
    document.Fields.Update()
    document.Repaginate()
    pages = document.ComputeStatistics(2)
    document.ExportAsFixedFormat(str(target), 17)
    print(f"Word pages: {pages}")
finally:
    if document is not None:
        document.Close(False)
    word.Quit()

reader = PdfReader(target)
details = []
for i, page in enumerate(reader.pages, 1):
    text = page.extract_text()
    details.append(dict(page=i, words=len(text.split()), text=text))
(folder / "render_audit.json").write_text(json.dumps(details, indent=2), encoding="utf-8")
pdf = pdfium.PdfDocument(target)
previews = folder / "previews"
previews.mkdir(exist_ok=True)
for i in range(len(pdf)):
    page = pdf[i]
    bitmap = page.render(scale=1.5)
    bitmap.to_pil().save(previews / f"page_{i+1}.png")
    bitmap.close()
    page.close()
pdf.close()
print(f"Exported {len(reader.pages)} PDF pages and preview images.")
for row in details:
    print(f"Page {row['page']}: {row['words']} words; {row['text'][:115]!r}")
