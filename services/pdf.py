"""
Common PDF helpers for ReportLab-based document generation.

These utilities are used by the service-layer PDF renderers so the route handlers
can stay focused on HTTP concerns.
"""

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate


def folio_size() -> tuple[float, float]:
    """Return Folio dimensions in points (8.5 x 13 inches)."""
    return (8.5 * inch, 13 * inch)


def create_folio_doc(buffer, header_func=None, footer_func=None) -> SimpleDocTemplate:
    """Create a SimpleDocTemplate using Folio page size and standard margins.

    Args:
        buffer: A writable file-like object (e.g. BytesIO).
        header_func: Optional callback to draw the header on each page.
        footer_func: Optional callback to draw the footer on each page.

    Returns:
        A configured SimpleDocTemplate instance.
    """
    width, height = folio_size()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(width, height),
        rightMargin=72,
        leftMargin=72,
        topMargin=100,
        bottomMargin=72,
    )
    return doc


def available_content_width(doc) -> float:
    """Return the available content width for a given doc."""
    return doc.pagesize[0] - doc.leftMargin - doc.rightMargin


def get_wrapped_style(font_size: int = 12, leading: int = 14) -> ParagraphStyle:
    """Return a base paragraph style with text wrapping."""
    styles = getSampleStyleSheet()
    return ParagraphStyle(
        "WrappedStyle",
        parent=styles["Normal"],
        fontSize=font_size,
        leading=leading,
        spaceBefore=0,
        spaceAfter=0,
    )


def get_justified_style(font_size: int = 12, leading: int = 14) -> ParagraphStyle:
    """Return a justified paragraph style for body text."""
    styles = getSampleStyleSheet()
    return ParagraphStyle(
        "JustifiedStyle",
        parent=styles["Normal"],
        fontSize=font_size,
        leading=leading,
        spaceAfter=12,
        alignment=4,  # 4 = justify
    )


def get_header_style(font_size: int = 12, leading: int = 14) -> ParagraphStyle:
    """Return a bold style for table headers and labels."""
    styles = getSampleStyleSheet()
    return ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontSize=font_size,
        leading=leading,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )


def get_bullet_style(font_size: int = 12, leading: int = 14) -> ParagraphStyle:
    """Return a paragraph style for bullet-point lists."""
    styles = getSampleStyleSheet()
    return ParagraphStyle(
        "BulletStyle",
        parent=styles["Normal"],
        fontSize=font_size,
        leading=leading,
        leftIndent=30,
        firstLineIndent=-12,
        spaceAfter=6,
    )


def draw_header_line(
    canvas, doc, y: float, length: float = 510, color: tuple[float, float, float] = (0x8C / 255, 0x04 / 255, 0x04 / 255)
) -> None:
    """Draw a horizontal line under the page header."""
    canvas.setStrokeColorRGB(*color)
    canvas.setLineWidth(2)
    line_start_x = (doc.width - length) / 2 + doc.leftMargin
    line_end_x = line_start_x + length
    canvas.line(line_start_x - 5, y, line_end_x, y)


def draw_footer(canvas, doc, label: str, reference: str = "UPHMO-CCS-GEN-912/rev0") -> None:
    """Draw a simple footer line and labels at the bottom of the page."""
    footer_y = doc.bottomMargin - 20
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.setLineWidth(1)
    canvas.line(doc.leftMargin, footer_y, doc.leftMargin + doc.width, footer_y)

    canvas.setFont("Helvetica", 12)
    canvas.drawString(doc.leftMargin, footer_y - 15, reference)
    label_width = canvas.stringWidth(label, "Helvetica", 12)
    canvas.drawString(doc.leftMargin + doc.width - label_width, footer_y - 15, label)
