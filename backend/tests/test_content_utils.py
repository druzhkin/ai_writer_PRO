"""
Tests for content utility functions.
"""

import pytest
from datetime import datetime

from app.utils.content_utils import (
    calculate_content_metrics, calculate_text_diff, validate_content_text,
    validate_content_title, sanitize_content_text, extract_content_keywords,
    format_content_for_export, generate_content_summary, calculate_content_similarity,
    extract_content_sections, validate_content_brief, generate_content_metadata,
    ContentMetrics
)


class TestContentMetrics:
    """Test cases for ContentMetrics dataclass."""
    
    def test_content_metrics_creation(self):
        """Test ContentMetrics creation."""
        metrics = ContentMetrics(
            word_count=100,
            character_count=500,
            character_count_no_spaces=400,
            sentence_count=5,
            paragraph_count=2,
            average_words_per_sentence=20.0,
            average_characters_per_word=5.0,
            reading_time_minutes=1
        )
        
        assert metrics.word_count == 100
        assert metrics.character_count == 500
        assert metrics.character_count_no_spaces == 400
        assert metrics.sentence_count == 5
        assert metrics.paragraph_count == 2
        assert metrics.average_words_per_sentence == 20.0
        assert metrics.average_characters_per_word == 5.0
        assert metrics.reading_time_minutes == 1


class TestCalculateContentMetrics:
    """Test cases for calculate_content_metrics function."""
    
    def test_calculate_metrics_basic_text(self):
        """Test metrics calculation for basic text."""
        text = "This is a test article. It has multiple sentences. Each sentence has different lengths."
        metrics = calculate_content_metrics(text)
        
        assert metrics.word_count > 0
        assert metrics.character_count > 0
        assert metrics.character_count_no_spaces < metrics.character_count
        assert metrics.sentence_count >= 3
        assert metrics.paragraph_count >= 1
        assert metrics.average_words_per_sentence > 0
        assert metrics.average_characters_per_word > 0
        assert metrics.reading_time_minutes >= 1
    
    def test_calculate_metrics_empty_text(self):
        """Test metrics calculation for empty text."""
        metrics = calculate_content_metrics("")
        
        assert metrics.word_count == 0
        assert metrics.character_count == 0
        assert metrics.character_count_no_spaces == 0
        assert metrics.sentence_count == 0
        assert metrics.paragraph_count == 0
        assert metrics.average_words_per_sentence == 0.0
        assert metrics.average_characters_per_word == 0.0
        assert metrics.reading_time_minutes == 0
    
    def test_calculate_metrics_whitespace_only(self):
        """Test metrics calculation for whitespace-only text."""
        metrics = calculate_content_metrics("   \n\n   ")
        
        assert metrics.word_count == 0
        assert metrics.character_count == 0
        assert metrics.character_count_no_spaces == 0
        assert metrics.sentence_count == 0
        assert metrics.paragraph_count == 0
        assert metrics.average_words_per_sentence == 0.0
        assert metrics.average_characters_per_word == 0.0
        assert metrics.reading_time_minutes == 0
    
    def test_calculate_metrics_multiple_paragraphs(self):
        """Test metrics calculation for multiple paragraphs."""
        text = """This is the first paragraph. It has multiple sentences.

This is the second paragraph. It also has multiple sentences.

This is the third paragraph."""
        
        metrics = calculate_content_metrics(text)
        
        assert metrics.paragraph_count == 3
        assert metrics.sentence_count >= 6
        assert metrics.word_count > 0
    
    def test_calculate_metrics_reading_time(self):
        """Test reading time calculation."""
        # Text with exactly 200 words
        text = "word " * 200
        metrics = calculate_content_metrics(text)
        
        assert metrics.reading_time_minutes == 1
        
        # Text with 400 words
        text = "word " * 400
        metrics = calculate_content_metrics(text)
        
        assert metrics.reading_time_minutes == 2


class TestCalculateTextDiff:
    """Test cases for calculate_text_diff function."""
    
    def test_diff_no_changes(self):
        """Test diff calculation with no changes."""
        text = "This is the same text."
        diff = calculate_text_diff(text, text)
        
        assert diff["has_changes"] is False
        assert diff["change_type"] == "none"
        assert diff["word_count_change"] == 0
        assert diff["character_count_change"] == 0
        assert diff["summary"] == "No changes"
    
    def test_diff_addition(self):
        """Test diff calculation with text addition."""
        original = ""
        new = "This is new content."
        diff = calculate_text_diff(original, new)
        
        assert diff["has_changes"] is True
        assert diff["change_type"] == "addition"
        assert diff["word_count_change"] == 4
        assert diff["character_count_change"] == 20
        assert "Added" in diff["summary"]
    
    def test_diff_deletion(self):
        """Test diff calculation with text deletion."""
        original = "This is content to be deleted."
        new = ""
        diff = calculate_text_diff(original, new)
        
        assert diff["has_changes"] is True
        assert diff["change_type"] == "deletion"
        assert diff["word_count_change"] == -6
        assert diff["character_count_change"] == -29
        assert "Removed" in diff["summary"]
    
    def test_diff_expansion(self):
        """Test diff calculation with text expansion."""
        original = "This is short text."
        new = "This is much longer text with additional content."
        diff = calculate_text_diff(original, new)
        
        assert diff["has_changes"] is True
        assert diff["change_type"] == "expansion"
        assert diff["word_count_change"] > 0
        assert diff["character_count_change"] > 0
        assert "expanded" in diff["summary"]
    
    def test_diff_contraction(self):
        """Test diff calculation with text contraction."""
        original = "This is much longer text with additional content."
        new = "This is short text."
        diff = calculate_text_diff(original, new)
        
        assert diff["has_changes"] is True
        assert diff["change_type"] == "contraction"
        assert diff["word_count_change"] < 0
        assert diff["character_count_change"] < 0
        assert "condensed" in diff["summary"]
    
    def test_diff_modification(self):
        """Test diff calculation with text modification."""
        original = "This is the original text."
        new = "This is the modified text."
        diff = calculate_text_diff(original, new)
        
        assert diff["has_changes"] is True
        assert diff["change_type"] == "modification"
        assert diff["word_count_change"] == 0
        assert diff["character_count_change"] == 0
        assert "modified" in diff["summary"]


class TestValidateContentText:
    """Test cases for validate_content_text function."""
    
    def test_validate_valid_text(self):
        """Test validation of valid text."""
        text = "This is a valid article with enough content to pass validation."
        is_valid, error = validate_content_text(text)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_empty_text(self):
        """Test validation of empty text."""
        is_valid, error = validate_content_text("")
        
        assert is_valid is False
        assert "empty" in error
    
    def test_validate_whitespace_only(self):
        """Test validation of whitespace-only text."""
        is_valid, error = validate_content_text("   \n\n   ")
        
        assert is_valid is False
        assert "whitespace" in error
    
    def test_validate_too_short(self):
        """Test validation of too short text."""
        text = "Short"
        is_valid, error = validate_content_text(text, min_length=100)
        
        assert is_valid is False
        assert "at least" in error
    
    def test_validate_too_long(self):
        """Test validation of too long text."""
        text = "word " * 10000  # Very long text
        is_valid, error = validate_content_text(text, max_length=1000)
        
        assert is_valid is False
        assert "exceed" in error
    
    def test_validate_too_few_words(self):
        """Test validation of text with too few words."""
        text = "word word"  # Only 2 words
        is_valid, error = validate_content_text(text)
        
        assert is_valid is False
        assert "10 words" in error
    
    def test_validate_excessive_repetition(self):
        """Test validation of text with excessive repetition."""
        text = "word " * 100  # 100 repetitions of the same word
        is_valid, error = validate_content_text(text)
        
        assert is_valid is False
        assert "repetition" in error


class TestValidateContentTitle:
    """Test cases for validate_content_title function."""
    
    def test_validate_valid_title(self):
        """Test validation of valid title."""
        title = "This is a valid title"
        is_valid, error = validate_content_title(title)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_empty_title(self):
        """Test validation of empty title."""
        is_valid, error = validate_content_title("")
        
        assert is_valid is False
        assert "empty" in error
    
    def test_validate_whitespace_title(self):
        """Test validation of whitespace-only title."""
        is_valid, error = validate_content_title("   ")
        
        assert is_valid is False
        assert "whitespace" in error
    
    def test_validate_too_short_title(self):
        """Test validation of too short title."""
        is_valid, error = validate_content_title("Hi")
        
        assert is_valid is False
        assert "3 characters" in error
    
    def test_validate_too_long_title(self):
        """Test validation of too long title."""
        title = "a" * 501  # 501 characters
        is_valid, error = validate_content_title(title)
        
        assert is_valid is False
        assert "500 characters" in error
    
    def test_validate_suspicious_title(self):
        """Test validation of suspicious title."""
        title = "a" * 100  # 100 characters without spaces
        is_valid, error = validate_content_title(title)
        
        assert is_valid is False
        assert "without spaces" in error


class TestSanitizeContentText:
    """Test cases for sanitize_content_text function."""
    
    def test_sanitize_normal_text(self):
        """Test sanitization of normal text."""
        text = "This is normal text with some content."
        sanitized = sanitize_content_text(text)
        
        assert sanitized == text
    
    def test_sanitize_excessive_whitespace(self):
        """Test sanitization of text with excessive whitespace."""
        text = "This   has    excessive     whitespace."
        sanitized = sanitize_content_text(text)
        
        assert "  " not in sanitized  # No double spaces
        assert "This has excessive whitespace." in sanitized
    
    def test_sanitize_excessive_newlines(self):
        """Test sanitization of text with excessive newlines."""
        text = "Line 1\n\n\n\n\nLine 2"
        sanitized = sanitize_content_text(text)
        
        assert "\n\n\n" not in sanitized  # No triple newlines
        assert "Line 1\n\nLine 2" in sanitized
    
    def test_sanitize_html_tags(self):
        """Test sanitization of HTML tags."""
        text = "This has <script>alert('xss')</script> and <b>bold</b> text."
        sanitized = sanitize_content_text(text)
        
        assert "<script>" not in sanitized
        assert "<b>" not in sanitized
        assert "This has" in sanitized
        assert "bold" in sanitized
    
    def test_sanitize_empty_text(self):
        """Test sanitization of empty text."""
        sanitized = sanitize_content_text("")
        assert sanitized == ""


class TestExtractContentKeywords:
    """Test cases for extract_content_keywords function."""
    
    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        text = "This article discusses artificial intelligence and machine learning technologies."
        keywords = extract_content_keywords(text)
        
        assert len(keywords) > 0
        assert "artificial" in keywords or "intelligence" in keywords
        assert "machine" in keywords or "learning" in keywords
    
    def test_extract_keywords_empty_text(self):
        """Test keyword extraction from empty text."""
        keywords = extract_content_keywords("")
        assert keywords == []
    
    def test_extract_keywords_max_limit(self):
        """Test keyword extraction with max limit."""
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11"
        keywords = extract_content_keywords(text, max_keywords=5)
        
        assert len(keywords) <= 5
    
    def test_extract_keywords_stop_words(self):
        """Test that stop words are filtered out."""
        text = "the and or but this that these those"
        keywords = extract_content_keywords(text)
        
        # Should have no keywords since all are stop words
        assert len(keywords) == 0
    
    def test_extract_keywords_short_words(self):
        """Test that short words are filtered out."""
        text = "a an it is be do go"
        keywords = extract_content_keywords(text)
        
        # Should have no keywords since all are short
        assert len(keywords) == 0


class TestFormatContentForExport:
    """Test cases for format_content_for_export function."""
    
    def test_format_markdown(self):
        """Test formatting for markdown export."""
        text = "Line 1\n\nLine 2"
        formatted = format_content_for_export(text, "markdown")
        
        assert formatted == text  # Should remain unchanged for markdown
    
    def test_format_html(self):
        """Test formatting for HTML export."""
        text = "Line 1\n\nLine 2"
        formatted = format_content_for_export(text, "html")
        
        assert "<p>" in formatted
        assert "</p>" in formatted
        assert "Line 1" in formatted
        assert "Line 2" in formatted
    
    def test_format_plain_text(self):
        """Test formatting for plain text export."""
        text = "This is plain text."
        formatted = format_content_for_export(text, "plain")
        
        assert formatted == text
    
    def test_format_empty_text(self):
        """Test formatting of empty text."""
        formatted = format_content_for_export("", "markdown")
        assert formatted == ""


class TestGenerateContentSummary:
    """Test cases for generate_content_summary function."""
    
    def test_generate_summary_basic(self):
        """Test basic summary generation."""
        text = "This is the first sentence. This is the second sentence. This is the third sentence."
        summary = generate_content_summary(text, max_length=50)
        
        assert len(summary) <= 50
        assert len(summary) > 0
        assert "This is" in summary
    
    def test_generate_summary_empty_text(self):
        """Test summary generation from empty text."""
        summary = generate_content_summary("")
        assert summary == ""
    
    def test_generate_summary_short_text(self):
        """Test summary generation from short text."""
        text = "Short text."
        summary = generate_content_summary(text, max_length=100)
        
        assert summary == "Short text."
    
    def test_generate_summary_respects_max_length(self):
        """Test that summary respects max length."""
        text = "This is a very long sentence that should be truncated when generating a summary."
        summary = generate_content_summary(text, max_length=20)
        
        assert len(summary) <= 20
        assert len(summary) > 0


class TestCalculateContentSimilarity:
    """Test cases for calculate_content_similarity function."""
    
    def test_similarity_identical_texts(self):
        """Test similarity of identical texts."""
        text = "This is identical text."
        similarity = calculate_content_similarity(text, text)
        
        assert similarity == 1.0
    
    def test_similarity_different_texts(self):
        """Test similarity of completely different texts."""
        text1 = "This is completely different text."
        text2 = "This is totally unrelated content."
        similarity = calculate_content_similarity(text1, text2)
        
        assert 0.0 <= similarity <= 1.0
        assert similarity < 1.0
    
    def test_similarity_empty_texts(self):
        """Test similarity of empty texts."""
        similarity = calculate_content_similarity("", "")
        assert similarity == 1.0
    
    def test_similarity_one_empty_text(self):
        """Test similarity when one text is empty."""
        text = "This is some text."
        similarity = calculate_content_similarity(text, "")
        
        assert similarity == 0.0
    
    def test_similarity_similar_texts(self):
        """Test similarity of similar texts."""
        text1 = "This is a test article about technology."
        text2 = "This is a test article about science."
        similarity = calculate_content_similarity(text1, text2)
        
        assert similarity > 0.5  # Should be quite similar


class TestExtractContentSections:
    """Test cases for extract_content_sections function."""
    
    def test_extract_sections_basic(self):
        """Test basic section extraction."""
        text = "First paragraph with content.\n\nSecond paragraph with different content."
        sections = extract_content_sections(text)
        
        assert len(sections) == 2
        assert sections[0]["index"] == 0
        assert sections[1]["index"] == 1
        assert "First paragraph" in sections[0]["content"]
        assert "Second paragraph" in sections[1]["content"]
    
    def test_extract_sections_empty_text(self):
        """Test section extraction from empty text."""
        sections = extract_content_sections("")
        assert sections == []
    
    def test_extract_sections_single_paragraph(self):
        """Test section extraction from single paragraph."""
        text = "This is a single paragraph."
        sections = extract_content_sections(text)
        
        assert len(sections) == 1
        assert sections[0]["index"] == 0
        assert sections[0]["word_count"] > 0
        assert len(sections[0]["keywords"]) >= 0
        assert len(sections[0]["summary"]) > 0


class TestValidateContentBrief:
    """Test cases for validate_content_brief function."""
    
    def test_validate_valid_brief(self):
        """Test validation of valid brief."""
        brief = "This is a valid brief with enough content."
        is_valid, error = validate_content_brief(brief)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_empty_brief(self):
        """Test validation of empty brief (should be valid as it's optional)."""
        is_valid, error = validate_content_brief("")
        assert is_valid is True
        assert error is None
    
    def test_validate_none_brief(self):
        """Test validation of None brief (should be valid as it's optional)."""
        is_valid, error = validate_content_brief(None)
        assert is_valid is True
        assert error is None
    
    def test_validate_whitespace_brief(self):
        """Test validation of whitespace-only brief."""
        is_valid, error = validate_content_brief("   ")
        assert is_valid is False
        assert "whitespace" in error
    
    def test_validate_too_short_brief(self):
        """Test validation of too short brief."""
        is_valid, error = validate_content_brief("Short")
        assert is_valid is False
        assert "10 characters" in error
    
    def test_validate_too_long_brief(self):
        """Test validation of too long brief."""
        brief = "a" * 5001  # 5001 characters
        is_valid, error = validate_content_brief(brief)
        assert is_valid is False
        assert "5000 characters" in error


class TestGenerateContentMetadata:
    """Test cases for generate_content_metadata function."""
    
    def test_generate_metadata_basic(self):
        """Test basic metadata generation."""
        text = "This is a test article with some content."
        title = "Test Article"
        brief = "This is a test brief."
        
        metadata = generate_content_metadata(text, title, brief)
        
        assert metadata["title"] == title
        assert metadata["brief"] == brief
        assert "summary" in metadata
        assert "metrics" in metadata
        assert "keywords" in metadata
        assert "sections" in metadata
        assert "generated_at" in metadata
        
        metrics = metadata["metrics"]
        assert metrics["word_count"] > 0
        assert metrics["character_count"] > 0
        assert metrics["sentence_count"] > 0
        assert metrics["paragraph_count"] > 0
        assert metrics["reading_time_minutes"] > 0
    
    def test_generate_metadata_without_brief(self):
        """Test metadata generation without brief."""
        text = "This is a test article."
        title = "Test Article"
        
        metadata = generate_content_metadata(text, title)
        
        assert metadata["title"] == title
        assert metadata["brief"] is None
        assert "metrics" in metadata
        assert "keywords" in metadata
    
    def test_generate_metadata_empty_text(self):
        """Test metadata generation with empty text."""
        text = ""
        title = "Empty Article"
        
        metadata = generate_content_metadata(text, title)
        
        assert metadata["title"] == title
        metrics = metadata["metrics"]
        assert metrics["word_count"] == 0
        assert metrics["character_count"] == 0
        assert metrics["sentence_count"] == 0
        assert metrics["paragraph_count"] == 0
        assert metrics["reading_time_minutes"] == 0
