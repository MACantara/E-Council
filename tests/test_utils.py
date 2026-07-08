"""
Tests for utility functions extracted during refactoring.
"""

import pytest
from decimal import Decimal, InvalidOperation


class TestHelpers:
    """Test general helper functions."""
    
    def test_safe_decimal_conversion_valid(self):
        """Test safe decimal conversion with valid input."""
        from utils.helpers import safe_decimal_conversion
        result = safe_decimal_conversion("123.45")
        assert result == Decimal("123.45")
    
    def test_safe_decimal_conversion_integer(self):
        """Test safe decimal conversion with integer."""
        from utils.helpers import safe_decimal_conversion
        result = safe_decimal_conversion(123)
        assert result == Decimal("123")
    
    def test_safe_decimal_conversion_invalid(self):
        """Test safe decimal conversion with invalid input."""
        from utils.helpers import safe_decimal_conversion
        result = safe_decimal_conversion("invalid")
        assert result == "invalid"
    
    def test_safe_decimal_conversion_none(self):
        """Test safe decimal conversion with None."""
        from utils.helpers import safe_decimal_conversion
        result = safe_decimal_conversion(None)
        assert result == "None"
    
    def test_allowed_image_file_valid(self):
        """Test image file validation with valid extensions."""
        from utils.helpers import allowed_image_file
        assert allowed_image_file("test.png") == True
        assert allowed_image_file("test.jpg") == True
        assert allowed_image_file("test.jpeg") == True
        assert allowed_image_file("test.gif") == True
    
    def test_allowed_image_file_invalid(self):
        """Test image file validation with invalid extensions."""
        from utils.helpers import allowed_image_file
        assert allowed_image_file("test.pdf") == False
        assert allowed_image_file("test.txt") == False
        assert allowed_image_file("test") == False
    
    def test_allowed_image_file_case_insensitive(self):
        """Test image file validation is case insensitive."""
        from utils.helpers import allowed_image_file
        assert allowed_image_file("test.PNG") == True
        assert allowed_image_file("test.JPG") == True


class TestFilters:
    """Test Jinja2 custom filters."""
    
    def test_truncate_text_short(self):
        """Test text truncation with short text."""
        from utils.filters import truncate_text
        result = truncate_text("Short text", length=100)
        assert result == "Short text"
    
    def test_truncate_text_long(self):
        """Test text truncation with long text."""
        from utils.filters import truncate_text
        result = truncate_text("This is a very long text that should be truncated", length=20)
        assert result == "This is a very lo..."
    
    def test_truncate_text_none(self):
        """Test text truncation with None."""
        from utils.filters import truncate_text
        result = truncate_text(None)
        assert result == ""
    
    def test_truncate_text_custom_suffix(self):
        """Test text truncation with custom suffix."""
        from utils.filters import truncate_text
        result = truncate_text("Long text here", length=10, suffix=">>")
        assert result == "Long text >>"
    
    def test_has_events_empty(self):
        """Test has_events with empty list."""
        from utils.filters import has_events
        result = has_events([], "First Semester", "2023-2024")
        assert result == False
    
    def test_has_events_matching(self):
        """Test has_events with matching events."""
        from utils.filters import has_events
        
        class MockEvent:
            def __init__(self, semester, year):
                self.events_semester = semester
                self.events_academic_year = year
        
        events = [
            MockEvent("First Semester", "2023-2024"),
            MockEvent("Second Semester", "2023-2024")
        ]
        result = has_events(events, "First Semester", "2023-2024")
        assert result == True
    
    def test_has_events_not_matching(self):
        """Test has_events with non-matching events."""
        from utils.filters import has_events
        
        class MockEvent:
            def __init__(self, semester, year):
                self.events_semester = semester
                self.events_academic_year = year
        
        events = [MockEvent("Second Semester", "2023-2024")]
        result = has_events(events, "First Semester", "2023-2024")
        assert result == False
    
    def test_has_resolutions_matching(self):
        """Test has_resolutions with matching resolutions."""
        from utils.filters import has_resolutions
        
        class MockResolution:
            def __init__(self, semester, year):
                self.board_resolutions_semester = semester
                self.board_resolutions_academic_year = year
        
        resolutions = [MockResolution("First Semester", "2023-2024")]
        result = has_resolutions(resolutions, "First Semester", "2023-2024")
        assert result == True
    
    def test_has_meetings_matching(self):
        """Test has_meetings with matching meetings."""
        from utils.filters import has_meetings
        
        class MockMeeting:
            def __init__(self, semester, year):
                self.minutes_of_the_meeting_semester = semester
                self.minutes_of_the_meeting_academic_year = year
        
        meetings = [MockMeeting("First Semester", "2023-2024")]
        result = has_meetings(meetings, "First Semester", "2023-2024")
        assert result == True
    
    def test_has_financial_reports_matching(self):
        """Test has_financial_reports with matching reports."""
        from utils.filters import has_financial_reports
        
        class MockReport:
            def __init__(self, semester, year):
                self.financial_reports_semester = semester
                self.financial_reports_academic_year = year
        
        reports = [MockReport("First Semester", "2023-2024")]
        result = has_financial_reports(reports, "First Semester", "2023-2024")
        assert result == True
    
    def test_has_papers_matching(self):
        """Test has_papers with matching papers."""
        from utils.filters import has_papers
        
        class MockPaper:
            def __init__(self, semester, year):
                self.concept_paper_forms_semester = semester
                self.concept_paper_forms_academic_year = year
        
        papers = [MockPaper("First Semester", "2023-2024")]
        result = has_papers(papers, "First Semester", "2023-2024")
        assert result == True
    
    def test_has_documentations_matching(self):
        """Test has_documentations with matching documentation."""
        from utils.filters import has_documentations
        
        class MockDoc:
            def __init__(self, semester, year):
                self.documentation_semester = semester
                self.documentation_academic_year = year
        
        documentations = [[MockDoc("First Semester", "2023-2024")]]
        result = has_documentations(documentations, "First Semester", "2023-2024")
        assert result == True