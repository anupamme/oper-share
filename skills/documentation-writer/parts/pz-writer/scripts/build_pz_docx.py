#!/usr/bin/env python3
"""Сборка пояснительной записки (docx) из markdown-исходника.

Собственный минимальный синтаксис (docx пишется только этим скриптом,
руками docx не правится):

  # ...            заголовок титула (по центру, 16 пт, жирный)
  ## ...           глава (14 пт, жирный)
  ### ...          параграф главы (14 пт, жирный)
  - ...            маркированный пункт
  N. ...           нумерованный пункт (висячий отступ)
  | a | b |        таблица (12 пт, шапка жирная)
  %%text           строка по центру
  %%               пустая строка
  %%pagebreak      разрыв страницы
  %%toc            поле оглавления (Word обновляет по F9)
Обычные строки — абзац с отступом 1,25 см.
**жирный** и «кавычки-ёлочки» распознаются автоматически.

Профили формата:
  nir      республиканский стандарт НИР: поля 3/1/2/2, интервал 1,0,
           нумерация страниц снизу по центру (лимит 15 страниц без приложений)
  school   школьный формат конкурсной работы: поля 2/1,25/2/2, интервал 1,0,
           без нумерации страниц

Запуск:
  python build_pz_docx.py md out.docx [--profile nir|school] [--spacing 1.5]
      [--margins left,right,top,bottom] [--page-numbers] [--font-size 14]
"""
import argparse
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = "Times New Roman"
BLACK = RGBColor(0, 0, 0)

PROFILES = {
    # margins: left, right, top, bottom (cm); spacing; page_numbers
    "nir": {"margins": (3, 1, 2, 2), "spacing": 1.0, "page_numbers": True},
    "school": {"margins": (2, 1.25, 2, 2), "spacing": 1.0, "page_numbers": False},
}


def setup(doc, margins, spacing):
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(14)
    normal.paragraph_format.line_spacing = spacing
    for sec in doc.sections:
        sec.left_margin = Cm(margins[0])
        sec.right_margin = Cm(margins[1])
        sec.top_margin = Cm(margins[2])
        sec.bottom_margin = Cm(margins[3])


def style_run(run, size=14, bold=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.color.rgb = BLACK
    if bold:
        run.bold = True
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rFonts.set(qn(attr), FONT)


class Builder:
    def __init__(self, doc, spacing):
        self.doc = doc
        self.spacing = spacing

    def add_runs(self, p, text, size=14, bold=False):
        """Добавляет текст, распознавая **жирный** и «кавычки-ёлочки»."""
        for seg in re.split(r"(\*\*.+?\*\*)", text):
            if not seg:
                continue
            b = bold
            if len(seg) > 4 and seg.startswith("**") and seg.endswith("**"):
                seg, b = seg[2:-2], True
            for piece in re.split(r"(«[^»]*»)", seg):
                if piece:
                    style_run(p.add_run(piece), size=size, bold=b)

    def heading(self, text, level, size):
        p = self.doc.add_heading(text, level=level)
        for r in p.runs:
            style_run(r, size=size, bold=True)
        return p

    def centered(self, text, size=14, bold=False):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = None
        p.paragraph_format.line_spacing = self.spacing
        self.add_runs(p, text, size=size, bold=bold)
        return p

    def body(self, text):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.25)
        p.paragraph_format.line_spacing = self.spacing
        self.add_runs(p, text)
        return p

    def bullet(self, text):
        p = self.doc.add_paragraph(style="List Bullet")
        p.paragraph_format.line_spacing = self.spacing
        self.add_runs(p, text)
        return p

    def numbered(self, text):
        p = self.doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Cm(1.0)
        pf.first_line_indent = Cm(-1.0)
        pf.line_spacing = self.spacing
        self.add_runs(p, text)
        return p

    def toc(self):
        """Поле оглавления по Heading 1-2; Word заполнит его при открытии."""
        p = self.doc.add_paragraph()
        fld = OxmlElement("w:fldSimple")
        fld.set(qn("w:instr"), r'TOC \o "1-2" \h \z \u')
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.text = "Оглавление (если пусто — выделить и нажать F9)"
        r.append(t)
        fld.append(r)
        p._p.append(fld)

    def table(self, rows):
        ncols = max(len(r) for r in rows)
        t = self.doc.add_table(rows=len(rows), cols=ncols)
        t.style = "Table Grid"
        for ri, row in enumerate(rows):
            for ci in range(ncols):
                cell_text = row[ci] if ci < len(row) else ""
                p = t.cell(ri, ci).paragraphs[0]
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.first_line_indent = None
                self.add_runs(p, cell_text, size=12, bold=(ri == 0))
        self.doc.add_paragraph()


def enable_update_fields(doc):
    el = OxmlElement("w:updateFields")
    el.set(qn("w:val"), "true")
    doc.settings.element.append(el)


def add_page_numbers(doc):
    """Поле PAGE по центру нижнего колонтитула."""
    for sec in doc.sections:
        p = sec.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fld = OxmlElement("w:fldSimple")
        fld.set(qn("w:instr"), "PAGE")
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.text = "1"
        r.append(t)
        fld.append(r)
        p._p.append(fld)


def build(md_text, out_path, profile, spacing, margins, page_numbers, font_size, title_size):
    doc = Document()
    setup(doc, margins, spacing)
    b = Builder(doc, spacing)
    lines = md_text.split("\n")
    stats = {"headings": 0, "tables": 0, "title_lines": 0}
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        if line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            rows = [r for r in block if not all(c and set(c) <= {"-", ":"} for c in r)]
            if rows:
                b.table(rows)
                stats["tables"] += 1
            continue
        if line.startswith("%%"):
            cmd = line[2:].strip()
            if cmd == "pagebreak":
                doc.add_page_break()
            elif cmd == "toc":
                b.toc()
            elif cmd:
                b.centered(cmd)
            else:
                doc.add_paragraph()
        elif line.startswith("### "):
            b.heading(line[4:], 2, font_size)
            stats["headings"] += 1
        elif line.startswith("## "):
            b.heading(line[3:], 1, font_size)
            stats["headings"] += 1
        elif line.startswith("# "):
            b.heading(line[2:], 0, title_size)
            stats["headings"] += 1
            stats["title_lines"] += 1
        elif line.startswith("- "):
            b.bullet(line[2:])
        elif re.match(r"^\d+\.\s", line):
            b.numbered(line)
        else:
            b.body(line)
        i += 1
    enable_update_fields(doc)
    if page_numbers:
        add_page_numbers(doc)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    stats["profile"] = profile
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("md", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--profile", choices=sorted(PROFILES), default="nir")
    ap.add_argument("--spacing", type=float, default=None, help="межстрочный (по умолчанию из профиля)")
    ap.add_argument("--margins", default=None, help="left,right,top,bottom в см")
    ap.add_argument("--page-numbers", action="store_true", default=None)
    ap.add_argument("--no-page-numbers", dest="page_numbers", action="store_false")
    ap.add_argument("--font-size", type=int, default=14)
    ap.add_argument("--title-size", type=int, default=16)
    args = ap.parse_args()

    prof = PROFILES[args.profile]
    spacing = args.spacing if args.spacing is not None else prof["spacing"]
    margins = tuple(float(x) for x in args.margins.split(",")) if args.margins else prof["margins"]
    page_numbers = prof["page_numbers"] if args.page_numbers is None else args.page_numbers
    if len(margins) != 4:
        sys.exit("--margins требует четыре числа: left,right,top,bottom")

    stats = build(args.md.read_text(encoding="utf-8"), args.out, args.profile, spacing,
                  margins, page_numbers, args.font_size, args.title_size)
    print(f"OK: {args.out} ({args.out.stat().st_size} bytes) | profile={stats['profile']} "
          f"headings={stats['headings']} tables={stats['tables']} "
          f"spacing={spacing} margins={margins} page_numbers={page_numbers}")


if __name__ == "__main__":
    main()
