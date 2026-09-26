"""
actions/file_generator.py — Universal Multi-Format Document Authoring Engine for JARVIS Mark 58
Empowers JARVIS to generate professional, executive-grade files on demand:
- Word Documents (.docx) with executive cover pages, styled headings, callout boxes, code blocks, and zebra-striped tables.
- PowerPoint Presentations (.pptx) with 16:9 widescreen layouts, cards, KPI callouts, and speaker notes.
- PDF Documents (.pdf) with clean typography, ReportLab NumberedCanvas (Page X of Y), tables, and cheat sheets.
- Excel Spreadsheets (.xlsx, .csv) with headers, automated formulas (SUM, AVERAGE), formatting, and auto-sized columns using OpenPyXL.
- Code & Text Files (.py, .md, .txt, .html, .tex, .json).
- Project & Codebase Documenter: Automatically documents entire code repositories or software architectures.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.ai_client import generate_text_with_retry

BASE_DIR = Path(__file__).resolve().parent.parent

def _get_output_dir(target_location: str = "desktop") -> Path:
    """Resolves target folder, default to Desktop."""
    loc = (target_location or "desktop").lower().strip()
    if loc in ("desktop", "desk"):
        cand = Path.home() / "OneDrive" / "Desktop"
        if cand.exists(): return cand
        return Path.home() / "Desktop"
    elif loc in ("downloads", "down"):
        cand = Path.home() / "OneDrive" / "Downloads"
        if cand.exists(): return cand
        return Path.home() / "Downloads"
    elif loc in ("documents", "docs"):
        cand = Path.home() / "OneDrive" / "Documents"
        if cand.exists(): return cand
        return Path.home() / "Documents"
    
    p = Path(target_location).expanduser()
    if p.exists() and p.is_dir():
        return p
    return Path.home() / "Desktop"


# ====================================================================
# 1. ENHANCED WORD DOCUMENT GENERATOR (.docx)
# ====================================================================
def create_word_document(
    filename: str,
    title: str,
    sections: List[Dict[str, Any]],
    output_dir: Optional[Path] = None,
    open_after: bool = True,
    subtitle: Optional[str] = None,
    author: str = "Akul Bhatnagar"
) -> str:
    """
    Creates an executive, professionally styled Word (.docx) document.
    sections: list of dicts:
      {
        "heading": "Section Heading",
        "level": 1,
        "content": "Body text...",
        "bullets": ["Point 1", "Point 2"],
        "callout": "Important takeaway or formula...",
        "code": "def solution(): ...",
        "table": [["Header 1", "Header 2"], ["Val 1", "Val 2"]]
      }
    """
    try:
        import docx
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import OxmlElement, parse_xml
        from docx.oxml.ns import qn, nsdecls

        if not filename.endswith(".docx"):
            filename += ".docx"

        out_dir = output_dir or _get_output_dir()
        file_path = out_dir / filename

        doc = docx.Document()

        # Page margins
        for section in doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.85)
            section.right_margin = Inches(0.85)

            # Running Header & Footer
            header = section.header
            hp = header.paragraphs[0]
            hp.text = f"{title[:45]} | J.A.R.V.I.S. Academic Intelligence"
            hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            for run in hp.runs:
                run.font.name = "Calibri"
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(148, 163, 184)

            footer = section.footer
            fp = footer.paragraphs[0]
            fp.text = f"Prepared for {author} • Confidential • {datetime.now().strftime('%B %d, %Y')}"
            fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in fp.runs:
                run.font.name = "Calibri"
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(148, 163, 184)

        # Title Block
        p_title = doc.add_paragraph()
        run_title = p_title.add_run(title)
        run_title.font.name = "Calibri"
        run_title.font.size = Pt(24)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(14, 116, 144)  # Stark Cyan/Teal
        p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT

        sub_text = subtitle or f"Autonomous Research & Executive Brief • Author: {author}"
        p_sub = doc.add_paragraph()
        run_sub = p_sub.add_run(sub_text)
        run_sub.font.name = "Calibri"
        run_sub.font.size = Pt(11)
        run_sub.font.italic = True
        run_sub.font.color.rgb = RGBColor(71, 85, 105)
        p_sub.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Decorative divider rule
        p_rule = doc.add_paragraph()
        p_rule_run = p_rule.add_run("―" * 48)
        p_rule_run.font.color.rgb = RGBColor(14, 116, 144)
        p_rule_run.font.bold = True
        p_rule.paragraph_format.space_after = Pt(14)

        for sec in sections:
            # 1. Heading
            h_text = sec.get("heading")
            if h_text:
                lvl = sec.get("level", 1)
                h = doc.add_heading(h_text, level=min(lvl, 3))
                h.paragraph_format.space_before = Pt(14)
                h.paragraph_format.space_after = Pt(4)
                for run in h.runs:
                    run.font.name = "Calibri"
                    if lvl == 1:
                        run.font.size = Pt(15)
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(15, 23, 42)  # Slate 900
                    else:
                        run.font.size = Pt(12.5)
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(14, 116, 144) # Teal

            # 2. Body Content
            content = sec.get("content")
            if content:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.line_spacing = 1.15
                r = p.add_run(content)
                r.font.name = "Calibri"
                r.font.size = Pt(11)
                r.font.color.rgb = RGBColor(51, 65, 85)

            # 3. Callout Box (Key Takeaway / Formula)
            callout = sec.get("callout")
            if callout:
                tbl = doc.add_table(rows=1, cols=1)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = tbl.cell(0, 0)
                cell.width = Inches(6.8)
                # Background fill & left border
                shd = parse_xml(r'<w:shd {} w:fill="F1F5F9"/>'.format(nsdecls('w')))
                cell._tc.get_or_add_tcPr().append(shd)
                borders = parse_xml(
                    r'<w:tcBorders {}><w:left w:val="single" w:sz="24" w:space="0" w:color="0E7490"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>'.format(nsdecls('w'))
                )
                cell._tc.get_or_add_tcPr().append(borders)
                cp = cell.paragraphs[0]
                cp.paragraph_format.space_before = Pt(6)
                cp.paragraph_format.space_after = Pt(6)
                c_run_badge = cp.add_run("⚡ KEY TAKEAWAY / FORMULA: ")
                c_run_badge.font.name = "Calibri"
                c_run_badge.font.size = Pt(10)
                c_run_badge.font.bold = True
                c_run_badge.font.color.rgb = RGBColor(14, 116, 144)
                c_run = cp.add_run(callout)
                c_run.font.name = "Calibri"
                c_run.font.size = Pt(10.5)
                c_run.font.italic = True
                c_run.font.color.rgb = RGBColor(30, 41, 59)
                doc.add_paragraph().paragraph_format.space_after = Pt(4)

            # 4. Code Block
            code_snippet = sec.get("code")
            if code_snippet:
                tbl_code = doc.add_table(rows=1, cols=1)
                cell_c = tbl_code.cell(0, 0)
                cell_c.width = Inches(6.8)
                shd_c = parse_xml(r'<w:shd {} w:fill="1E293B"/>'.format(nsdecls('w')))
                cell_c._tc.get_or_add_tcPr().append(shd_c)
                p_code = cell_c.paragraphs[0]
                p_code.paragraph_format.space_before = Pt(6)
                p_code.paragraph_format.space_after = Pt(6)
                run_c = p_code.add_run(code_snippet)
                run_c.font.name = "Consolas"
                run_c.font.size = Pt(9.5)
                run_c.font.color.rgb = RGBColor(226, 232, 240)
                doc.add_paragraph().paragraph_format.space_after = Pt(4)

            # 5. Bullet Points
            bullets = sec.get("bullets", [])
            for b in bullets:
                p = doc.add_paragraph(style='List Bullet')
                p.paragraph_format.space_after = Pt(3)
                r = p.add_run(b)
                r.font.name = "Calibri"
                r.font.size = Pt(10.5)
                r.font.color.rgb = RGBColor(51, 65, 85)

            # 6. Formatted Table
            table_data = sec.get("table")
            if table_data and isinstance(table_data, list) and len(table_data) > 0:
                rows = len(table_data)
                cols = len(table_data[0])
                table = doc.add_table(rows=rows, cols=cols)
                table.style = 'Table Grid'
                table.alignment = WD_TABLE_ALIGNMENT.CENTER

                for r_idx, row in enumerate(table_data):
                    for c_idx, val in enumerate(row):
                        cell = table.cell(r_idx, c_idx)
                        cell.text = str(val)
                        if r_idx == 0:
                            # Header row: dark navy background with bold white text
                            shd = parse_xml(r'<w:shd {} w:fill="0F172A"/>'.format(nsdecls('w')))
                            cell._tc.get_or_add_tcPr().append(shd)
                            for p in cell.paragraphs:
                                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                for run in p.runs:
                                    run.font.name = "Calibri"
                                    run.font.bold = True
                                    run.font.size = Pt(10)
                                    run.font.color.rgb = RGBColor(255, 255, 255)
                        else:
                            # Alternating zebra striping
                            if r_idx % 2 == 1:
                                shd = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls('w')))
                                cell._tc.get_or_add_tcPr().append(shd)
                            for p in cell.paragraphs:
                                for run in p.runs:
                                    run.font.name = "Calibri"
                                    run.font.size = Pt(9.5)
                                    run.font.color.rgb = RGBColor(51, 65, 85)

                doc.add_paragraph().paragraph_format.space_after = Pt(6)

        doc.save(str(file_path))

        if open_after:
            try:
                os.startfile(str(file_path))
            except Exception:
                pass

        return f"Successfully generated Executive Word Document: '{file_path.name}' at {file_path.parent}"

    except Exception as e:
        return f"Failed to generate Word document: {e}"


# ====================================================================
# 2. ENHANCED POWERPOINT PRESENTATION (.pptx)
# ====================================================================
def create_presentation(
    filename: str,
    title: str,
    subtitle: str,
    slides_data: List[Dict[str, Any]],
    output_dir: Optional[Path] = None,
    open_after: bool = True
) -> str:
    """
    Creates an executive 16:9 widescreen PowerPoint presentation (.pptx).
    slides_data: list of dicts:
      {
        "title": "Slide Title",
        "type": "bullets" | "comparison" | "kpi",
        "bullets": ["Point 1", "Point 2"],
        "col1_title": "...", "col1_bullets": [...],
        "col2_title": "...", "col2_bullets": [...],
        "kpi_val": "98.5%", "kpi_label": "Accuracy Metric",
        "notes": "Speaker notes"
      }
    """
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN

        if not filename.endswith(".pptx"):
            filename += ".pptx"

        out_dir = output_dir or _get_output_dir()
        file_path = out_dir / filename

        prs = Presentation()
        # Set 16:9 widescreen layout
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        # Slide 1: Executive Title Slide
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        t_box = slide.shapes.title
        s_box = slide.placeholders[1]

        t_box.text = title
        s_box.text = f"{subtitle}\nAuthored with J.A.R.V.I.S. Mark 58 • {datetime.now().strftime('%B %d, %Y')}"

        # Style Title
        for p in t_box.text_frame.paragraphs:
            p.font.name = "Calibri"
            p.font.size = Pt(40)
            p.font.bold = True
            p.font.color.rgb = RGBColor(14, 116, 144)

        # Content Slides
        bullet_slide_layout = prs.slide_layouts[1]
        for s_info in slides_data:
            s_title = s_info.get("title", "Key Concept")
            s_type = s_info.get("type", "bullets").lower()
            bullets = s_info.get("bullets", [])
            notes_text = s_info.get("notes", "")

            c_slide = prs.slides.add_slide(bullet_slide_layout)
            c_slide.shapes.title.text = s_title
            c_slide.shapes.title.text_frame.paragraphs[0].font.name = "Calibri"
            c_slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(28)
            c_slide.shapes.title.text_frame.paragraphs[0].font.bold = True
            c_slide.shapes.title.text_frame.paragraphs[0].font.color.rgb = RGBColor(15, 23, 42)

            body_shape = c_slide.placeholders[1]
            tf = body_shape.text_frame
            tf.word_wrap = True

            if s_type == "kpi":
                kpi_val = s_info.get("kpi_val", "100%")
                kpi_lbl = s_info.get("kpi_label", "Key Benchmark")
                p1 = tf.paragraphs[0]
                p1.text = kpi_val
                p1.font.size = Pt(56)
                p1.font.bold = True
                p1.font.color.rgb = RGBColor(14, 116, 144)
                p1.alignment = PP_ALIGN.CENTER

                p2 = tf.add_paragraph()
                p2.text = kpi_lbl
                p2.font.size = Pt(20)
                p2.font.italic = True
                p2.alignment = PP_ALIGN.CENTER

                if bullets:
                    tf.add_paragraph().text = ""
                    for b in bullets:
                        bp = tf.add_paragraph()
                        bp.text = f"• {b}"
                        bp.font.size = Pt(16)
            elif s_type == "comparison":
                c1_title = s_info.get("col1_title", "Perspective A")
                c1_pts = s_info.get("col1_bullets", [])
                c2_title = s_info.get("col2_title", "Perspective B")
                c2_pts = s_info.get("col2_bullets", [])

                p_c1 = tf.paragraphs[0]
                p_c1.text = f"▶ {c1_title.upper()}:"
                p_c1.font.bold = True
                p_c1.font.size = Pt(18)
                p_c1.font.color.rgb = RGBColor(14, 116, 144)
                for pt in c1_pts:
                    bp = tf.add_paragraph()
                    bp.text = f"  • {pt}"
                    bp.font.size = Pt(15)

                tf.add_paragraph().text = ""
                p_c2 = tf.add_paragraph()
                p_c2.text = f"▶ {c2_title.upper()}:"
                p_c2.font.bold = True
                p_c2.font.size = Pt(18)
                p_c2.font.color.rgb = RGBColor(79, 70, 229)
                for pt in c2_pts:
                    bp = tf.add_paragraph()
                    bp.text = f"  • {pt}"
                    bp.font.size = Pt(15)
            else:
                for idx, b_text in enumerate(bullets):
                    p = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
                    p.text = b_text
                    p.level = 0
                    p.font.name = "Calibri"
                    p.font.size = Pt(19)
                    p.font.color.rgb = RGBColor(51, 65, 85)

            if notes_text:
                c_slide.notes_slide.notes_text_frame.text = notes_text

        prs.save(str(file_path))

        if open_after:
            try:
                os.startfile(str(file_path))
            except Exception:
                pass

        return f"Successfully generated 16:9 Presentation: '{file_path.name}' ({len(slides_data) + 1} slides) at {file_path.parent}"

    except Exception as e:
        return f"Failed to generate PowerPoint presentation: {e}"


# ====================================================================
# 3. ENHANCED PDF GENERATOR (ReportLab with NumberedCanvas)
# ====================================================================
def create_pdf_document(
    filename: str,
    title: str,
    sections: List[Dict[str, Any]],
    output_dir: Optional[Path] = None,
    open_after: bool = True
) -> str:
    """
    Creates a high-fidelity PDF document with ReportLab and page numbering.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfgen import canvas

        if not filename.endswith(".pdf"):
            filename += ".pdf"

        out_dir = output_dir or _get_output_dir()
        file_path = out_dir / filename

        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_header_footer(num_pages)
                    super().showPage()
                super().save()

            def draw_header_footer(self, page_count):
                self.saveState()
                self.setFont("Helvetica", 8)
                self.setFillColor(colors.HexColor("#64748b"))
                # Running Header
                self.drawString(54, 11 * 72 - 36, title[:50])
                self.drawRightString(8.5 * 72 - 54, 11 * 72 - 36, "J.A.R.V.I.S. Mark 58 Academic Core")
                self.setStrokeColor(colors.HexColor("#cbd5e1"))
                self.setLineWidth(0.5)
                self.line(54, 11 * 72 - 40, 8.5 * 72 - 54, 11 * 72 - 40)
                # Footer
                self.drawString(54, 36, "Confidential • Akul Bhatnagar")
                self.drawRightString(8.5 * 72 - 54, 36, f"Page {self._pageNumber} of {page_count}")
                self.restoreState()

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            rightMargin=54, leftMargin=54,
            topMargin=54, bottomMargin=54
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0e7490'),
            spaceAfter=8
        )
        sub_style = ParagraphStyle(
            'DocSub',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=14
        )
        heading_style = ParagraphStyle(
            'SecHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=12,
            spaceAfter=5
        )
        body_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14.5,
            textColor=colors.HexColor('#334155'),
            spaceAfter=6
        )
        bullet_style = ParagraphStyle(
            'BulletCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13.5,
            leftIndent=14,
            firstLineIndent=-10,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=3
        )
        callout_style = ParagraphStyle(
            'CalloutCustom',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#0e7490')
        )

        story = []
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Autonomous Academic Dossier • Generated {datetime.now().strftime('%B %d, %Y')}", sub_style))
        story.append(Spacer(1, 10))

        for sec in sections:
            h = sec.get("heading")
            if h:
                story.append(Paragraph(h, heading_style))

            content = sec.get("content")
            if content:
                story.append(Paragraph(content, body_style))

            callout = sec.get("callout")
            if callout:
                c_tbl = Table([[Paragraph(f"<b>TAKEAWAY:</b> {callout}", callout_style)]], colWidths=[500])
                c_tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
                    ('LINELEFT', (0,0), (0,0), 3, colors.HexColor('#0e7490')),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('LEFTPADDING', (0,0), (-1,-1), 8),
                ]))
                story.append(Spacer(1, 4))
                story.append(c_tbl)
                story.append(Spacer(1, 6))

            bullets = sec.get("bullets", [])
            for b in bullets:
                story.append(Paragraph(f"&bull; {b}", bullet_style))

            tbl_data = sec.get("table")
            if tbl_data and isinstance(tbl_data, list) and len(tbl_data) > 0:
                wrapped_table = []
                for row_idx, r in enumerate(tbl_data):
                    wrapped_row = []
                    for val in r:
                        style_to_use = heading_style if row_idx == 0 else body_style
                        wrapped_row.append(Paragraph(str(val), style_to_use))
                    wrapped_table.append(wrapped_row)

                t = Table(wrapped_table)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                ]))
                story.append(Spacer(1, 6))
                story.append(t)
                story.append(Spacer(1, 8))

        doc.build(story, canvasmaker=NumberedCanvas)

        if open_after:
            try:
                os.startfile(str(file_path))
            except Exception:
                pass

        return f"Successfully generated Executive PDF Document: '{file_path.name}' at {file_path.parent}"

    except Exception as e:
        return f"Failed to generate PDF document: {e}"


# ====================================================================
# 4. ENHANCED EXCEL SPREADSHEET GENERATOR (.xlsx)
# ====================================================================
def create_excel_sheet(
    filename: str,
    title: str,
    columns: List[str],
    rows: List[List[Any]],
    output_dir: Optional[Path] = None,
    open_after: bool = True,
    add_summary_row: bool = True
) -> str:
    """
    Creates an Excel spreadsheet (.xlsx) with styles and automated summary formulas.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        if not filename.endswith(".xlsx"):
            filename += ".xlsx"

        out_dir = output_dir or _get_output_dir()
        file_path = out_dir / filename

        wb = Workbook()
        ws = wb.active
        ws.title = title[:30] if title else "Sheet1"

        # Headers
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="0E7490", end_color="0E7490", fill_type="solid")
        border_thin = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        ws.append(columns)
        for col_idx in range(1, len(columns) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Rows
        for r_data in rows:
            ws.append(r_data)

        # Style data cells and format
        for row in ws.iter_rows(min_row=2, max_row=len(rows)+1, min_col=1, max_col=len(columns)):
            for cell in row:
                cell.font = Font(name="Calibri", size=10)
                cell.border = border_thin
                if isinstance(cell.value, (int, float)):
                    cell.alignment = Alignment(horizontal="right")

        # Optional automated summary row for numeric columns
        if add_summary_row and rows:
            summary_row = []
            num_rows = len(rows)
            for c_idx in range(1, len(columns) + 1):
                col_letter = get_column_letter(c_idx)
                # Check if first data row is float/int
                sample = rows[0][c_idx - 1] if len(rows[0]) >= c_idx else None
                if c_idx == 1:
                    summary_row.append("Total / Summary")
                elif isinstance(sample, (int, float)):
                    summary_row.append(f"=SUM({col_letter}2:{col_letter}{num_rows+1})")
                else:
                    summary_row.append("")
            ws.append(summary_row)
            # Style summary row
            sum_row_idx = num_rows + 2
            for c_idx in range(1, len(columns) + 1):
                cell = ws.cell(row=sum_row_idx, column=c_idx)
                cell.font = Font(name="Calibri", size=11, bold=True, color="0F172A")
                cell.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
                cell.border = Border(top=Side(style='thin', color='0F172A'), bottom=Side(style='double', color='0F172A'))

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

        wb.save(str(file_path))

        if open_after:
            try:
                os.startfile(str(file_path))
            except Exception:
                pass

        return f"Successfully generated Excel Spreadsheet: '{file_path.name}' at {file_path.parent}"

    except Exception as e:
        return f"Failed to generate Excel sheet: {e}"


# ====================================================================
# 5. PROJECT & CODEBASE DOCUMENTATION ENGINE
# ====================================================================
def document_codebase(
    project_path: str,
    output_format: str = "docx",
    output_filename: Optional[str] = None,
    open_after: bool = True
) -> str:
    """
    Reads an entire repository/project and generates a comprehensive
    technical documentation manual, architecture breakdown, and API spec.
    """
    p = Path(project_path).resolve()
    if not p.exists() or not p.is_dir():
        return f"Specified project path does not exist: {project_path}"

    files_summary = []
    tree_items = []
    
    # Read README if available
    readme_content = ""
    for r in ["README.md", "README.txt", "readme.md"]:
        if (p / r).exists():
            try:
                readme_content = (p / r).read_text(encoding="utf-8", errors="ignore")[:4000]
                break
            except Exception:
                pass

    # Scan python, js, html, or config files
    for root, dirs, files in os.walk(p):
        dirs[:] = [d for d in dirs if d not in (".git", "venv", ".venv", "__pycache__", "build", "dist", "node_modules")]
        rel_root = Path(root).relative_to(p)
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in (".py", ".json", ".sql", ".md", ".bat", ".sh", ".spec", ".js", ".html"):
                full_f = Path(root) / f
                rel_f = str(rel_root / f) if str(rel_root) != "." else f
                tree_items.append(rel_f)
                if len(files_summary) < 15 and full_f.stat().st_size < 100000:
                    try:
                        content_sample = full_f.read_text(encoding="utf-8", errors="ignore")[:1000]
                        files_summary.append(f"File: {rel_f}\n```\n{content_sample}\n```")
                    except Exception:
                        pass

    project_name = p.name
    files_tree_str = "\n".join(tree_items[:50])
    samples_str = "\n\n".join(files_summary[:8])

    prompt = (
        f"You are J.A.R.V.I.S., Chief Software Architect.\n"
        f"Generate a comprehensive, technical software documentation manual for the project '{project_name}'.\n\n"
        f"README Context:\n{readme_content}\n\n"
        f"Directory Tree:\n{files_tree_str}\n\n"
        f"Source Code Samples:\n{samples_str}\n\n"
        "Provide a deeply rigorous, structured documentation report with:\n"
        "1. System Architecture & High-Level Design (Core pillars, runtime workflows, tech stack)\n"
        "2. Module & File Breakdown (Purpose of each key component)\n"
        "3. Database & State Schema (Tables, models, keys, state management)\n"
        "4. Key Functions & API Interface Specifications\n"
        "5. Deployment, Execution & Integration Guide\n"
        "6. Security & Performance Best Practices"
    )

    doc_text = generate_text_with_retry(prompt)

    out_name = output_filename or f"{project_name}_Technical_Documentation"
    out_dir = _get_output_dir("desktop")

    if output_format.lower() in ("docx", "word"):
        # Convert markdown-like response into structured Word sections
        sections = []
        cur_sec = {"heading": "1. System Overview", "content": ""}
        for line in doc_text.splitlines():
            line_str = line.strip()
            if line_str.startswith("# ") or line_str.startswith("## ") or (len(line_str) > 3 and line_str[:2] in ("1.", "2.", "3.", "4.", "5.", "6.") and line_str[2] == " "):
                if cur_sec["content"].strip() or cur_sec.get("bullets"):
                    sections.append(cur_sec)
                cur_sec = {"heading": line_str.lstrip("#").strip(), "content": "", "bullets": []}
            elif line_str.startswith("- ") or line_str.startswith("* "):
                cur_sec.setdefault("bullets", []).append(line_str[2:].strip())
            else:
                cur_sec["content"] += line + "\n"
        if cur_sec["content"].strip() or cur_sec.get("bullets"):
            sections.append(cur_sec)

        return create_word_document(
            filename=f"{out_name}.docx",
            title=f"{project_name.upper()} — Technical Specification & Architecture Manual",
            sections=sections,
            output_dir=out_dir,
            open_after=open_after
        )
    elif output_format.lower() == "pdf":
        sections = [{"heading": "Technical Architecture", "content": doc_text}]
        return create_pdf_document(
            filename=f"{out_name}.pdf",
            title=f"{project_name} Technical Manual",
            sections=sections,
            output_dir=out_dir,
            open_after=open_after
        )
    else:
        # Markdown
        md_file = out_dir / f"{out_name}.md"
        md_file.write_text(f"# {project_name} — Technical Architecture Manual\n\n{doc_text}", encoding="utf-8")
        if open_after:
            try: os.startfile(str(md_file))
            except Exception: pass
        return f"Successfully generated Markdown Documentation: '{md_file.name}' at {md_file.parent}"


# ====================================================================
# 6. UNIVERSAL DISPATCHER
# ====================================================================
def universal_file_creator(parameters: dict, player=None) -> str:
    """
    Main tool handler for creating any file requested by the user.
    parameters:
      file_type: 'docx' | 'pptx' | 'pdf' | 'xlsx' | 'code' | 'markdown' | 'project_doc'
      filename: e.g. 'Project_Blueprint.docx'
      title: Title of document or presentation
      content: Raw text or structured body
      sections: Optional list of sections
      slides: Optional list of slide data for presentations
      columns: Optional list of column names for Excel
      rows: Optional list of row lists for Excel
      target_location: 'desktop' | 'downloads' | 'documents'
      project_path: Optional path for documenting a codebase
      open_after: True to auto-open file
    """
    params = parameters or {}
    ftype = (params.get("file_type") or "docx").lower().strip()
    fname = (params.get("filename") or "Document").strip()
    title = (params.get("title") or fname.replace("_", " ").title()).strip()
    content = params.get("content") or ""
    loc = params.get("target_location") or "desktop"
    open_after = params.get("open_after", True)
    out_dir = _get_output_dir(loc)

    if player and hasattr(player, "write_log"):
        player.write_log(f"FILE GEN: Generating {ftype.upper()} file '{fname}' in {loc}...")

    # 1. Project / Codebase Documenter
    if ftype in ("project_doc", "codebase_doc", "doc_code"):
        proj_p = params.get("project_path") or str(BASE_DIR)
        doc_fmt = params.get("format") or "docx"
        return document_codebase(proj_p, output_format=doc_fmt, output_filename=fname, open_after=open_after)

    # 2. Word Document
    if ftype in ("docx", "word", "doc"):
        secs = params.get("sections")
        if not secs:
            # Parse raw content into clean sections
            secs = []
            cur = {"heading": "Overview", "content": ""}
            for line in content.splitlines():
                if line.startswith("# ") or line.startswith("## ") or (len(line) > 3 and line[:2] in ("1.", "2.", "3.", "4.", "5.", "6.") and line[2] == " "):
                    if cur["content"].strip():
                        secs.append(cur)
                    cur = {"heading": line.lstrip("#").strip(), "content": "", "bullets": []}
                elif line.startswith("- ") or line.startswith("* "):
                    cur.setdefault("bullets", []).append(line[2:].strip())
                else:
                    cur["content"] += line + "\n"
            if cur["content"].strip() or cur.get("bullets"):
                secs.append(cur)
        return create_word_document(fname, title, secs, output_dir=out_dir, open_after=open_after)

    # 3. PowerPoint Presentation
    elif ftype in ("pptx", "powerpoint", "presentation", "slides"):
        slides_data = params.get("slides")
        if not slides_data:
            slides_data = []
            cur_s = {"title": "Key Concept", "bullets": []}
            for line in content.splitlines():
                l_str = line.strip()
                if l_str.startswith("# ") or l_str.startswith("## ") or (len(l_str) > 3 and l_str[:2] in ("1.", "2.", "3.", "4.", "5.") and l_str[2] == " "):
                    if cur_s["bullets"] or cur_s["title"] != "Key Concept":
                        slides_data.append(cur_s)
                    cur_s = {"title": l_str.lstrip("#").strip(), "bullets": []}
                elif l_str.startswith("- ") or l_str.startswith("* ") or l_str.startswith("• "):
                    cur_s["bullets"].append(l_str[2:].strip())
            if cur_s["bullets"] or cur_s["title"] != "Key Concept":
                slides_data.append(cur_s)

        if not slides_data:
            slides_data = [
                {"title": "Core Architecture", "bullets": ["High-throughput autonomous systems", "Sub-150ms real-time audio pipeline"]},
                {"title": "Summary & Next Steps", "bullets": ["Deployment verification complete", "Multi-modal orchestration active"]}
            ]
        sub = params.get("subtitle") or "Prepared by J.A.R.V.I.S. Mark 58"
        return create_presentation(fname, title, sub, slides_data, output_dir=out_dir, open_after=open_after)

    # 4. PDF Document
    elif ftype in ("pdf",):
        secs = params.get("sections")
        if not secs:
            secs = [{"heading": title, "content": content}]
        return create_pdf_document(fname, title, secs, output_dir=out_dir, open_after=open_after)

    # 5. Excel Spreadsheet
    elif ftype in ("xlsx", "excel", "spreadsheet", "csv"):
        cols = params.get("columns") or ["Item", "Category", "Metric", "Notes"]
        rows = params.get("rows") or [["Sample 1", "General", 100, "Verified"]]
        return create_excel_sheet(fname, title, cols, rows, output_dir=out_dir, open_after=open_after)

    # 6. Plain Code or Markdown File
    else:
        ext = ftype if ftype.startswith(".") else f".{ftype}"
        if not fname.endswith(ext):
            fname += ext
        target_file = out_dir / fname
        target_file.write_text(content, encoding="utf-8")
        if open_after:
            try:
                os.startfile(str(target_file))
            except Exception:
                pass
        return f"Successfully generated file: '{target_file.name}' at {target_file.parent}"
