"""
Content processing utilities for text analysis, validation, and formatting.
"""

import re
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import difflib
from dataclasses import dataclass


@dataclass
class ContentMetrics:
    """Content metrics data class."""
    word_count: int
    character_count: int
    character_count_no_spaces: int
    sentence_count: int
    paragraph_count: int
    average_words_per_sentence: float
    average_characters_per_word: float
    reading_time_minutes: int


def calculate_content_metrics(text: str) -> ContentMetrics:
    """
    Calculate comprehensive content metrics.
    
    Args:
        text: Content text to analyze
        
    Returns:
        ContentMetrics object with calculated metrics
    """
    if not text or not text.strip():
        return ContentMetrics(0, 0, 0, 0, 0, 0.0, 0.0, 0)
    
    # Basic counts
    word_count = len(text.split())
    character_count = len(text)
    character_count_no_spaces = len(text.replace(' ', ''))
    
    # Sentence count (simple heuristic)
    sentences = re.split(r'[.!?]+', text)
    sentence_count = len([s for s in sentences if s.strip()])
    
    # Paragraph count
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    paragraph_count = len(paragraphs)
    
    # Averages
    average_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
    average_characters_per_word = character_count / word_count if word_count > 0 else 0
    
    # Reading time (assuming 200 words per minute)
    reading_time_minutes = max(1, word_count // 200)
    
    return ContentMetrics(
        word_count=word_count,
        character_count=character_count,
        character_count_no_spaces=character_count_no_spaces,
        sentence_count=sentence_count,
        paragraph_count=paragraph_count,
        average_words_per_sentence=average_words_per_sentence,
        average_characters_per_word=average_characters_per_word,
        reading_time_minutes=reading_time_minutes
    )


def calculate_text_diff(original_text: str, new_text: str) -> Dict[str, Any]:
    """
    Calculate detailed diff between two texts.
    
    Args:
        original_text: Original text
        new_text: New text
        
    Returns:
        Dictionary with diff information
    """
    if not original_text and not new_text:
        return {
            "has_changes": False,
            "change_type": "none",
            "word_count_change": 0,
            "character_count_change": 0,
            "diff_lines": [],
            "summary": "No changes"
        }
    
    if not original_text:
        return {
            "has_changes": True,
            "change_type": "addition",
            "word_count_change": len(new_text.split()),
            "character_count_change": len(new_text),
            "diff_lines": [f"+ {line}" for line in new_text.split('\n')],
            "summary": f"Added {len(new_text.split())} words"
        }
    
    if not new_text:
        return {
            "has_changes": True,
            "change_type": "deletion",
            "word_count_change": -len(original_text.split()),
            "character_count_change": -len(original_text),
            "diff_lines": [f"- {line}" for line in original_text.split('\n')],
            "summary": f"Removed {len(original_text.split())} words"
        }
    
    # Calculate word and character changes
    original_words = len(original_text.split())
    new_words = len(new_text.split())
    word_count_change = new_words - original_words
    
    original_chars = len(original_text)
    new_chars = len(new_text)
    character_count_change = new_chars - original_chars
    
    # Generate unified diff
    diff_lines = list(difflib.unified_diff(
        original_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile='original',
        tofile='new',
        lineterm=''
    ))
    
    # Determine change type
    if word_count_change > 0:
        change_type = "expansion"
    elif word_count_change < 0:
        change_type = "contraction"
    else:
        change_type = "modification"
    
    # Generate summary
    if abs(word_count_change) > 0:
        summary = f"Content {change_type} by {abs(word_count_change)} words"
    else:
        summary = "Content modified with same word count"
    
    return {
        "has_changes": True,
        "change_type": change_type,
        "word_count_change": word_count_change,
        "character_count_change": character_count_change,
        "diff_lines": diff_lines,
        "summary": summary
    }


def validate_content_text(text: str, min_length: int = 100, max_length: int = 50000) -> Tuple[bool, Optional[str]]:
    """
    Validate content text for length and quality.
    
    Args:
        text: Text to validate
        min_length: Minimum character length
        max_length: Maximum character length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return False, "Content text cannot be empty"
    
    if not text.strip():
        return False, "Content text cannot be only whitespace"
    
    if len(text) < min_length:
        return False, f"Content must be at least {min_length} characters long"
    
    if len(text) > max_length:
        return False, f"Content cannot exceed {max_length} characters"
    
    # Check for suspicious patterns
    if len(text.split()) < 10:
        return False, "Content must have at least 10 words"
    
    # Check for excessive repetition
    words = text.lower().split()
    if len(words) > 0:
        word_frequency = {}
        for word in words:
            word_frequency[word] = word_frequency.get(word, 0) + 1
        
        max_frequency = max(word_frequency.values())
        if max_frequency > len(words) * 0.3:  # More than 30% repetition
            return False, "Content appears to have excessive word repetition"
    
    return True, None


def validate_content_title(title: str) -> Tuple[bool, Optional[str]]:
    """
    Validate content title.
    
    Args:
        title: Title to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title:
        return False, "Title cannot be empty"
    
    if not title.strip():
        return False, "Title cannot be only whitespace"
    
    if len(title) < 3:
        return False, "Title must be at least 3 characters long"
    
    if len(title) > 500:
        return False, "Title cannot exceed 500 characters"
    
    # Check for suspicious patterns
    if title.count(' ') == 0 and len(title) > 50:
        return False, "Title appears to be too long without spaces"
    
    return True, None


def sanitize_content_text(text: str) -> str:
    """
    Sanitize content text by removing potentially harmful content.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Remove potential script tags (basic protection)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove potential style tags
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove HTML tags (basic)
    text = re.sub(r'<[^>]+>', '', text)
    
    return text.strip()


def extract_content_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from content text.
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Simple keyword extraction (can be enhanced with NLP libraries)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
        'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'must', 'can', 'shall', 'a', 'an', 'some', 'any', 'all', 'both', 'each',
        'every', 'other', 'another', 'such', 'no', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'just', 'now', 'here', 'there', 'when',
        'where', 'why', 'how', 'what', 'which', 'who', 'whom', 'whose'
    }
    
    # Count word frequency
    word_frequency = {}
    for word in words:
        if word not in stop_words and len(word) > 2:
            word_frequency[word] = word_frequency.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_frequency.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:max_keywords]]


def format_content_for_export(text: str, format_type: str = "markdown") -> str:
    """
    Format content for export in different formats.
    
    Args:
        text: Content text to format
        format_type: Export format (markdown, html, plain)
        
    Returns:
        Formatted content
    """
    if not text:
        return ""
    
    if format_type.lower() == "markdown":
        # Basic markdown formatting
        # Convert line breaks to markdown
        formatted = text.replace('\n\n', '\n\n')
        return formatted
    
    elif format_type.lower() == "html":
        # Basic HTML formatting
        # Convert line breaks to HTML
        formatted = text.replace('\n\n', '</p><p>')
        formatted = f"<p>{formatted}</p>"
        return formatted
    
    else:  # plain text
        return text


def generate_content_summary(text: str, max_length: int = 200) -> str:
    """
    Generate a summary of content text.
    
    Args:
        text: Content text to summarize
        max_length: Maximum length of summary
        
    Returns:
        Content summary
    """
    if not text:
        return ""
    
    # Simple extractive summarization (first few sentences)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return ""
    
    summary = ""
    for sentence in sentences:
        if len(summary + sentence) <= max_length:
            summary += sentence + ". "
        else:
            break
    
    return summary.strip()


def calculate_content_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two content texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 and not text2:
        return 1.0
    
    if not text1 or not text2:
        return 0.0
    
    # Use SequenceMatcher for similarity
    matcher = difflib.SequenceMatcher(None, text1, text2)
    return matcher.ratio()


def extract_content_sections(text: str) -> List[Dict[str, Any]]:
    """
    Extract sections from content text.
    
    Args:
        text: Content text to analyze
        
    Returns:
        List of sections with metadata
    """
    if not text:
        return []
    
    # Split by double newlines (paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    sections = []
    for i, paragraph in enumerate(paragraphs):
        metrics = calculate_content_metrics(paragraph)
        keywords = extract_content_keywords(paragraph, max_keywords=5)
        
        sections.append({
            "index": i,
            "content": paragraph,
            "word_count": metrics.word_count,
            "character_count": metrics.character_count,
            "keywords": keywords,
            "summary": generate_content_summary(paragraph, max_length=100)
        })
    
    return sections


def validate_content_brief(brief: str) -> Tuple[bool, Optional[str]]:
    """
    Validate content brief/outline.
    
    Args:
        brief: Brief text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not brief:
        return True, None  # Brief is optional
    
    if not brief.strip():
        return False, "Brief cannot be only whitespace"
    
    if len(brief) > 5000:
        return False, "Brief cannot exceed 5000 characters"
    
    if len(brief) < 10:
        return False, "Brief must be at least 10 characters long"
    
    return True, None


def generate_content_metadata(text: str, title: str, brief: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate comprehensive metadata for content.
    
    Args:
        text: Content text
        title: Content title
        brief: Optional content brief
        
    Returns:
        Dictionary with content metadata
    """
    metrics = calculate_content_metrics(text)
    keywords = extract_content_keywords(text)
    sections = extract_content_sections(text)
    summary = generate_content_summary(text)
    
    return {
        "title": title,
        "brief": brief,
        "summary": summary,
        "metrics": {
            "word_count": metrics.word_count,
            "character_count": metrics.character_count,
            "sentence_count": metrics.sentence_count,
            "paragraph_count": metrics.paragraph_count,
            "reading_time_minutes": metrics.reading_time_minutes,
            "average_words_per_sentence": round(metrics.average_words_per_sentence, 2),
            "average_characters_per_word": round(metrics.average_characters_per_word, 2)
        },
        "keywords": keywords,
        "sections": sections,
        "generated_at": datetime.utcnow().isoformat()
    }
