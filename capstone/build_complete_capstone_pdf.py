"""
Generates the Capstone Project PDF Report
for Priyanshu Pandey (Roll No: 2501730051, K = 51).
"""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable, Image as RLImage, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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
        self.setFillColor(colors.HexColor("#555555"))

        if self._pageNumber > 1:
            self.drawString(54, 750, "NAND TO TETRIS - I (ETCNTC301) | CAPSTONE PROJECT REPORT")
            self.drawRightString(612 - 54, 750, "Priyanshu Pandey (2501730051)")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

            self.line(54, 45, 612 - 54, 45)
            self.drawString(54, 32, "Priyanshu Pandey (2501730051) | K = 51 | Nand to Tetris Capstone")
            self.drawRightString(612 - 54, 32, f"Page {self._pageNumber} of {page_count}")

        self.restoreState()


def build_pdf():
    pdf_filename = os.path.join(BASE_DIR, "Priyanshu_Pandey_2501730051_Capstone_Report.pdf")
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CoverTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=22, leading=28, alignment=1, textColor=colors.HexColor("#0B2545")
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle", parent=styles["Normal"], fontName="Helvetica",
        fontSize=11, leading=16, alignment=1, textColor=colors.HexColor("#1E3A8A")
    )
    h1_style = ParagraphStyle(
        "Heading1_Custom", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=13, leading=17, spaceBefore=12, spaceAfter=6,
        textColor=colors.HexColor("#0B2545"), keepWithNext=True
    )
    h2_style = ParagraphStyle(
        "Heading2_Custom", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=4,
        textColor=colors.HexColor("#1E3A8A"), keepWithNext=True
    )
    body_style = ParagraphStyle(
        "Body_Custom", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=13, spaceAfter=5, textColor=colors.HexColor("#1E293B")
    )
    header_cell_style = ParagraphStyle(
        "HeaderCell_Custom", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=9, leading=12, textColor=colors.white
    )
    code_style = ParagraphStyle(
        "Code_Custom", parent=styles["Normal"], fontName="Courier",
        fontSize=7.0, leading=8.9, textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F1F5F9"), borderPadding=5,
        spaceBefore=3, spaceAfter=6
    )

    story = [
        Spacer(1, 20),
        Paragraph("NAND TO TETRIS - I (ETCNTC301) | CAPSTONE PROJECT REPORT", subtitle_style),
        Spacer(1, 6),
        Paragraph("Make the Computer Draw a Box", title_style),
        Paragraph("School of Engineering & Technology, K.R. Mangalam University", subtitle_style),
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0B2545"), spaceAfter=14),
    ]

    summary_data = [
        [
            Paragraph("Student Information", header_cell_style),
            Paragraph("Details", header_cell_style),
            Paragraph("Project Parameter", header_cell_style),
            Paragraph("Calculated Value", header_cell_style),
        ],
        [
            Paragraph("<b>Name</b>", body_style),
            Paragraph("Priyanshu Pandey", body_style),
            Paragraph("<b>Personal Number (K)</b>", body_style),
            Paragraph("<b>51</b> (Last two digits of Roll No.)", body_style),
        ],
        [
            Paragraph("<b>Course & Branch</b>", body_style),
            Paragraph("B.Tech CSE (AI/ML)", body_style),
            Paragraph("<b>Assembler Feature (K mod 3)</b>", body_style),
            Paragraph("51 mod 3 = <b>0</b> (Save <code>symbols.txt</code>)", body_style),
        ],
        [
            Paragraph("<b>Roll Number</b>", body_style),
            Paragraph("2501730051", body_style),
            Paragraph("<b>Box Size & Row</b>", body_style),
            Paragraph("Row <b>51</b>, Height <b>20</b>, Width <b>64 px</b> (4 words)", body_style),
        ],
    ]
    t_info = Table(summary_data, colWidths=[105, 115, 130, 154])
    t_info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B2545")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>Overview & Personal Number (K = 51):</b> For this project, I built the Hack computer in HDL, "
        "wrote a two-pass assembler in Python, and created a Hack assembly program (<code>Box.asm</code>) "
        "that shows a 64 x 20 black rectangle at row 51 (start address 18016) when any key is pressed and clears it when released.",
        body_style
    ))

    story.append(Paragraph("1. Part A: Building the Hack Computer (HDL)", h1_style))
    with open(os.path.join(BASE_DIR, "Part_A", "Memory.hdl"), "r", encoding="utf-8") as f:
        story.append(Paragraph("1.1 Memory Module (Memory.hdl)", h2_style))
        story.append(Preformatted(f.read().strip(), code_style))

    with open(os.path.join(BASE_DIR, "Part_A", "CPU.hdl"), "r", encoding="utf-8") as f:
        story.append(Paragraph("1.2 CPU & Top-Level Computer (CPU.hdl & Computer.hdl)", h2_style))
        story.append(Preformatted(f.read().strip(), code_style))

    with open(os.path.join(BASE_DIR, "Part_A", "Computer.hdl"), "r", encoding="utf-8") as f:
        story.append(Preformatted(f.read().strip(), code_style))

    story.append(PageBreak())
    story.append(Paragraph("2. Part B: Python Assembler (assembler.py)", h1_style))
    story.append(Paragraph(
        "Since <code>51 mod 3 = 0</code>, <code>assembler.py</code> saves all predefined symbols, ROM labels, "
        "and RAM variables with their decimal addresses into <code>symbols.txt</code> via <code>save_symbols_file</code>:",
        body_style
    ))
    excerpt = (
        "def save_symbols_file(output_dir: str, symbol_table: dict[str, int]) -> str:\n"
        "    symbols_path = os.path.join(output_dir, \"symbols.txt\")\n"
        "    with open(symbols_path, \"w\", encoding=\"utf-8\") as f:\n"
        "        for name, addr in symbol_table.items():\n"
        "            f.write(f\"{name}: {addr}\\n\")\n"
        "    return symbols_path"
    )
    story.append(Preformatted(excerpt, code_style))

    with open(os.path.join(BASE_DIR, "Part_C", "symbols.txt"), "r", encoding="utf-8") as f:
        story.append(Paragraph("Exported symbols.txt for Box.asm (K = 51):", h2_style))
        story.append(Preformatted(f.read().strip(), code_style))

    story.append(Paragraph("3. Part C: Box Drawing Program (Box.asm)", h1_style))
    with open(os.path.join(BASE_DIR, "Part_C", "Box.asm"), "r", encoding="utf-8") as f:
        story.append(Preformatted(f.read().strip(), code_style))

    shot_path = os.path.join(BASE_DIR, "Part_C", "screenshots", "box_key_pressed.png")
    if os.path.exists(shot_path):
        story.append(Paragraph("CPU Emulator Screen Output (Key Pressed - 64x20 Box at Row 51):", h2_style))
        story.append(RLImage(shot_path, width=420, height=238))
        story.append(Spacer(1, 8))

    story.append(Paragraph("4. One Mistake I Fixed", h1_style))
    story.append(Paragraph(
        "<b>Problem:</b> Using only one pointer variable (<code>wordAddr</code>) across the 4 words per row "
        "without resetting it back to the start of the row produced a slanted staircase shape.<br/>"
        "<b>Fix:</b> Separated tracking into <code>rowAddr</code> (incremented by 32 after each row) and "
        "<code>wordAddr</code> (reset to <code>rowAddr</code> at the start of every row loop), producing straight vertical edges.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully built: {pdf_filename}")


if __name__ == "__main__":
    build_pdf()
