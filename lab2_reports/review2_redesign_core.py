# build_review2_redesign.py
"""
MediPaw Review 2 PowerPoint Redesign Generator
Course: 23CSE473 - Neural Networks and Deep Learning (Semester VII)
Design System: Review 1 Visual Identity (MediPaw_Team11.pptx)
- White / warm-white backgrounds (#FFFFFF, #FAFAF9)
- Maroon / burgundy (#B6114D, #800020), muted coral/red (#C00000, #E15B64), subtle pale-pink accents (#FDF2F4, #FCE7F3)
- Bold, professional black headings (#111827)
- Consistent typography (Aptos / Arial)
- Clean academic presentation style with varied non-repetitive layouts
- Top-right MediPaw logo on every slide with exact tagline: "every paw deserves a chance"
- Generates:
  1. MediPaw_Review2_AC_Sanhitha_Reddy.pptx (44 slides) + PDF
  2. MediPaw_Review2_Shaik_Abdus_Sattar.pptx (44 slides) + PDF
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# -----------------------------------------------------------------------------
# Color Palette Constants (Review 1 Maroon & Academic Identity)
# -----------------------------------------------------------------------------
COLOR_MAROON = RGBColor(182, 17, 77)     # #B6114D - Primary Brand Accent
COLOR_BURGUNDY = RGBColor(128, 0, 32)    # #800020 - Deep Academic Wine
COLOR_CRIMSON = RGBColor(192, 0, 0)      # #C00000 - Key Highlights
COLOR_TEAL = RGBColor(8, 96, 114)        # #086072 - MediPaw Brand Secondary
COLOR_DARK = RGBColor(17, 24, 39)        # #111827 - Primary Headings
COLOR_BODY = RGBColor(55, 65, 81)        # #374151 - Body Text
COLOR_MUTED = RGBColor(107, 114, 128)    # #6B7280 - Captions / Footers
COLOR_WHITE = RGBColor(255, 255, 255)    # #FFFFFF - Pure White
COLOR_WARM_BG = RGBColor(253, 251, 247)  # #FDFBF7 - Warm White / Ivory
COLOR_ROSE_TINT = RGBColor(253, 242, 244)# #FDF2F4 - Subtle Pale Pink Accent
COLOR_BORDER = RGBColor(229, 231, 235)   # #E5E7EB - Card & Table Borders
COLOR_BORDER_ROSE = RGBColor(244, 207, 215) # Subtle Rose Border

FONT_HEADING = "Aptos"
FONT_BODY = "Aptos"

LOGO_PATH = os.path.abspath("lab2_reports/figures/Logo.png")

# -----------------------------------------------------------------------------
# Helper Functions: Drawing Shapes, Text, and Formatting
# -----------------------------------------------------------------------------
def set_slide_background(slide, color=COLOR_WHITE):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_header(slide, title_text, category_text, slide_num, total_slides, student_name, roll_no):
    """
    Standard header on technical slides:
    - Top-right official logo (with exact aspect ratio, clear of headers)
    - Category / Module breadcrumb
    - Bold slide title
    - Subtle horizontal hairline divider
    - Professional academic footer
    """
    # 1. Top-Right Logo
    if os.path.exists(LOGO_PATH):
        # Logo placed at top-right with margin
        slide.shapes.add_picture(LOGO_PATH, Inches(10.85), Inches(0.22), width=Inches(2.15), height=Inches(0.75))

    # 2. Header Text Box (Category + Slide Title)
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(9.8), Inches(0.85))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = FONT_HEADING
    p_cat.font.size = Pt(9.5)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_MAROON
    p_cat.space_after = Pt(2)

    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_DARK

    # 3. Subtle hairline rule below header
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.28), Inches(11.7), Inches(0.015))
    rule.fill.solid()
    rule.fill.fore_color.rgb = COLOR_BORDER
    rule.line.color.rgb = COLOR_BORDER

    # Small maroon accent pip under the title
    pip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.27), Inches(1.2), Inches(0.035))
    pip.fill.solid()
    pip.fill.fore_color.rgb = COLOR_MAROON
    pip.line.color.rgb = COLOR_MAROON

    # 4. Standard Footer
    footer_rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(6.90), Inches(11.7), Inches(0.015))
    footer_rule.fill.solid()
    footer_rule.fill.fore_color.rgb = COLOR_BORDER
    footer_rule.line.color.rgb = COLOR_BORDER

    # Footer Left: Brand & Tagline
    f_left = slide.shapes.add_textbox(Inches(0.8), Inches(6.95), Inches(5.0), Inches(0.35))
    tf_fl = f_left.text_frame
    tf_fl.word_wrap = False
    tf_fl.margin_left = tf_fl.margin_top = tf_fl.margin_right = tf_fl.margin_bottom = 0
    p_fl = tf_fl.paragraphs[0]
    p_fl.text = "MediPaw — every paw deserves a chance"
    p_fl.font.name = FONT_BODY
    p_fl.font.size = Pt(9)
    p_fl.font.color.rgb = COLOR_MUTED

    # Footer Center: Student Details & Course
    f_center = slide.shapes.add_textbox(Inches(5.0), Inches(6.95), Inches(4.5), Inches(0.35))
    tf_fc = f_center.text_frame
    tf_fc.word_wrap = False
    tf_fc.margin_left = tf_fc.margin_top = tf_fc.margin_right = tf_fc.margin_bottom = 0
    p_fc = tf_fc.paragraphs[0]
    p_fc.alignment = PP_ALIGN.CENTER
    p_fc.text = f"{student_name} ({roll_no}) | 23CSE473 Review 2"
    p_fc.font.name = FONT_BODY
    p_fc.font.size = Pt(9)
    p_fc.font.color.rgb = COLOR_MUTED

    # Footer Right: Slide Number
    f_right = slide.shapes.add_textbox(Inches(10.5), Inches(6.95), Inches(2.0), Inches(0.35))
    tf_fr = f_right.text_frame
    tf_fr.word_wrap = False
    tf_fr.margin_left = tf_fr.margin_top = tf_fr.margin_right = tf_fr.margin_bottom = 0
    p_fr = tf_fr.paragraphs[0]
    p_fr.alignment = PP_ALIGN.RIGHT
    p_fr.text = f"Slide {slide_num} of {total_slides}"
    p_fr.font.name = FONT_BODY
    p_fr.font.size = Pt(9)
    p_fr.font.bold = True
    p_fr.font.color.rgb = COLOR_MAROON

def add_card(slide, left, top, width, height, bg_color=COLOR_WHITE, border_color=COLOR_BORDER, border_width=1):
    """Adds a clean card shape with subtle border."""
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(border_width)
    else:
        card.line.fill.background()
    return card

def add_callout_box(slide, left, top, width, height, title, body, bg_color=COLOR_ROSE_TINT, accent_color=COLOR_MAROON):
    """Creates a distinguished callout box with a colored left accent border."""
    card = add_card(slide, left, top, width, height, bg_color=bg_color, border_color=COLOR_BORDER_ROSE)
    # Left accent bar
    accent_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, Inches(0.08), height)
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = accent_color
    accent_bar.line.fill.background()

    tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.12), width - Inches(0.35), height - Inches(0.24))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.name = FONT_HEADING
    p_title.font.size = Pt(11.5)
    p_title.font.bold = True
    p_title.font.color.rgb = accent_color
    p_title.space_after = Pt(3)

    p_body = tf.add_paragraph()
    p_body.text = body
    p_body.font.name = FONT_BODY
    p_body.font.size = Pt(10.5)
    p_body.font.color.rgb = COLOR_BODY
    return card

def add_bullets(tf, bullet_list, font_size=11, space_after=5):
    """Helper to populate formatted bullet points in a text frame."""
    for idx, item in enumerate(bullet_list):
        if idx == 0 and len(tf.paragraphs) == 1 and tf.paragraphs[0].text == "":
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        
        p.space_after = Pt(space_after)
        p.font.name = FONT_BODY
        p.font.size = Pt(font_size)
        
        # Check if item has a bold lead-in like "Lead In: Content"
        if ":" in item and not item.startswith("http"):
            parts = item.split(":", 1)
            run1 = p.add_run()
            run1.text = "• " + parts[0] + ":"
            run1.font.bold = True
            run1.font.color.rgb = COLOR_DARK
            
            run2 = p.add_run()
            run2.text = parts[1]
            run2.font.bold = False
            run2.font.color.rgb = COLOR_BODY
        else:
            run = p.add_run()
            run.text = "• " + item
            run.font.bold = False
            run.font.color.rgb = COLOR_BODY

def add_table(slide, left, top, width, height, headers, rows, col_widths=None):
    """Adds a clean, professional academic table styled in maroon."""
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, height)
    table = table_shape.table

    if col_widths and len(col_widths) == num_cols:
        for idx, w in enumerate(col_widths):
            table.columns[idx].width = w

    # Format Header Row
    for col_idx, header in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_MAROON
        p = cell.text_frame.paragraphs[0]
        p.text = header
        p.alignment = PP_ALIGN.LEFT
        p.font.name = FONT_HEADING
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    # Format Data Rows
    for row_idx, row_data in enumerate(rows):
        bg = COLOR_ROSE_TINT if (row_idx % 2 == 1) else COLOR_WHITE
        for col_idx, val in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.text = str(val)
            p.alignment = PP_ALIGN.LEFT
            p.font.name = FONT_BODY
            p.font.size = Pt(10)
            p.font.color.rgb = COLOR_DARK if col_idx == 0 else COLOR_BODY
            if col_idx == 0:
                p.font.bold = True

    return table_shape

print("Review 2 Redesign Helper library defined successfully.")
