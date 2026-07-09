"""Unit tests for the common PDF helpers."""

from io import BytesIO
from unittest.mock import MagicMock

from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate

from services import pdf


def test_folio_size():
    width, height = pdf.folio_size()
    assert width == 8.5 * inch
    assert height == 13 * inch


def test_create_folio_doc():
    buffer = BytesIO()
    doc = pdf.create_folio_doc(buffer)
    assert isinstance(doc, SimpleDocTemplate)
    assert doc.pagesize == pdf.folio_size()
    assert doc.leftMargin == 72
    assert doc.rightMargin == 72
    assert doc.topMargin == 100
    assert doc.bottomMargin == 72


def test_available_content_width():
    buffer = BytesIO()
    doc = pdf.create_folio_doc(buffer)
    expected = pdf.folio_size()[0] - doc.leftMargin - doc.rightMargin
    assert pdf.available_content_width(doc) == expected


def test_get_wrapped_style():
    style = pdf.get_wrapped_style(font_size=11, leading=13)
    assert style.fontSize == 11
    assert style.leading == 13
    assert style.name == "WrappedStyle"


def test_get_justified_style():
    style = pdf.get_justified_style(font_size=11, leading=13)
    assert style.fontSize == 11
    assert style.leading == 13
    assert style.alignment == 4


def test_get_header_style():
    style = pdf.get_header_style(font_size=11, leading=13)
    assert style.fontName == "Helvetica-Bold"
    assert style.fontSize == 11


def test_get_bullet_style():
    style = pdf.get_bullet_style(font_size=11, leading=13)
    assert style.leftIndent == 30
    assert style.firstLineIndent == -12


def test_draw_header_line():
    mock_canvas = MagicMock()
    buffer = BytesIO()
    doc = pdf.create_folio_doc(buffer)
    pdf.draw_header_line(mock_canvas, doc, y=50)
    mock_canvas.setStrokeColorRGB.assert_called_once()
    mock_canvas.setLineWidth.assert_called_once_with(2)
    mock_canvas.line.assert_called_once()


def test_draw_footer():
    mock_canvas = MagicMock()
    mock_canvas.stringWidth.return_value = 20
    buffer = BytesIO()
    doc = pdf.create_folio_doc(buffer)
    pdf.draw_footer(mock_canvas, doc, "Test Label")
    mock_canvas.line.assert_called_once()
    mock_canvas.drawString.assert_called()
