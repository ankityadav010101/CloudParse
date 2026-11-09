"""Build the Cloud Command Parser project report PDF."""
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                KeepTogether, Paragraph, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "report/report-template.md"
OUT = ROOT / "report/report.pdf"
NAVY = colors.HexColor("#16324F")
TEAL = colors.HexColor("#187C80")
PALE = colors.HexColor("#EAF1F5")


def style_set():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name="CoverTitle", parent=s["Title"], fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=NAVY, alignment=TA_LEFT, spaceAfter=10))
    s.add(ParagraphStyle(name="SubtitleX", parent=s["Normal"], fontSize=12, leading=16, textColor=TEAL, spaceAfter=14))
    s.add(ParagraphStyle(name="H1X", parent=s["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=NAVY, spaceBefore=7, spaceAfter=7, keepWithNext=True))
    s.add(ParagraphStyle(name="H2X", parent=s["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=TEAL, spaceBefore=6, spaceAfter=4, keepWithNext=True))
    s.add(ParagraphStyle(name="BodyX", parent=s["BodyText"], fontSize=8.6, leading=12, textColor=colors.HexColor("#263746"), spaceAfter=5))
    s.add(ParagraphStyle(name="CellX", parent=s["BodyText"], fontSize=7.1, leading=8.7, textColor=colors.HexColor("#263746")))
    s.add(ParagraphStyle(name="CellHeadX", parent=s["CellX"], fontName="Helvetica-Bold", textColor=colors.white))
    return s


def markup(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"https?://[^\s]+", lambda m: f'<link href="{m.group(0)}" color="#187C80">{m.group(0)}</link>', text)
    return text


def parse_table(lines, st):
    rows = []
    for line in lines:
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append([Paragraph(markup(c), st["CellHeadX"] if not rows else st["CellX"]) for c in cells])
    n = max(map(len, rows))
    widths = [174 * mm / n] * n
    # Keep tables readable, with a little extra room for prose-heavy cells.
    if n == 2:
        widths = [60 * mm, 114 * mm]
    elif n == 3:
        widths = [43 * mm, 43 * mm, 88 * mm]
    elif n == 5:
        widths = [37 * mm, 27 * mm, 30 * mm, 30 * mm, 50 * mm]
    elif n == 6:
        widths = [19 * mm, 21 * mm, 33 * mm, 42 * mm, 33 * mm, 26 * mm]
    t = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C7D2DA")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, PALE]),
        ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4), ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    return t


def build():
    st = style_set()
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story, i, first_h1 = [], 0, True
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i]); i += 1
            story.append(parse_table(block, st)); story.append(Spacer(1, 4))
            continue
        if line.startswith("# "):
            story.append(Paragraph(markup(line[2:]), st["CoverTitle"])); i += 1; continue
        if line.startswith("## "):
            title = line[3:]
            if title.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                if title.startswith("2."):
                    story.append(PageBreak())
                if not first_h1:
                    story.append(Spacer(1, 3))
                first_h1 = False
                story.append(Paragraph(markup(title), st["H1X"]))
            else:
                story.append(Paragraph(markup(title), st["SubtitleX"] if len(story) < 2 else st["H2X"]))
            i += 1; continue
        if line.startswith("- "):
            story.append(Paragraph("&bull; " + markup(line[2:]), st["BodyX"])); i += 1; continue
        if line == "---":
            story.append(PageBreak()); i += 1; continue
        paragraph = Paragraph(markup(line), st["BodyX"])
        if line.startswith("Sequence-level distillation is suited"):
            story.append(KeepTogether([paragraph]))
        else:
            story.append(paragraph)
        i += 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=17*mm, bottomMargin=10*mm, title="Cloud Command Parser Project Report", author="Ankit Yadav")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#536575"))
        canvas.drawRightString(192*mm, 5*mm, f"{doc.page}")
        canvas.restoreState()
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=footer)])
    doc.build(story)
    print(OUT)

if __name__ == "__main__":
    build()
