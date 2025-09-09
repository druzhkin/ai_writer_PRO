"""
Utility functions for style analysis and text processing.
"""

import re
import string
from typing import Dict, List, Any, Tuple
from collections import Counter
import math


def preprocess_text(text: str) -> str:
    """
    Preprocess text for style analysis.
    
    Args:
        text: Raw text to preprocess
        
    Returns:
        Preprocessed text
    """
    if not text:
        return ""
    
    # Remove extra whitespace and normalize line breaks
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    text = re.sub(r'[.]{3,}', '...', text)
    
    return text.strip()


def normalize_text_for_analysis(text: str) -> str:
    """
    Normalize text for consistent analysis.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase for analysis
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-"\']', '', text)
    
    return text.strip()


def calculate_readability_metrics(text: str) -> Dict[str, float]:
    """
    Calculate readability metrics for text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary of readability metrics
    """
    if not text:
        return {}
    
    # Split into sentences and words
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    words = text.split()
    words = [w.strip(string.punctuation) for w in words if w.strip(string.punctuation)]
    
    if not sentences or not words:
        return {}
    
    # Basic metrics
    total_sentences = len(sentences)
    total_words = len(words)
    total_syllables = sum(count_syllables(word) for word in words)
    
    # Average sentence length
    avg_sentence_length = total_words / total_sentences
    
    # Average syllables per word
    avg_syllables_per_word = total_syllables / total_words
    
    # Flesch Reading Ease Score
    flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    
    # Flesch-Kincaid Grade Level
    fk_grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
    
    # Automated Readability Index
    ari = (4.71 * (len(text) / total_words)) + (0.5 * (total_words / total_sentences)) - 21.43
    
    return {
        "flesch_reading_ease": round(flesch_score, 2),
        "flesch_kincaid_grade": round(fk_grade, 2),
        "automated_readability_index": round(ari, 2),
        "avg_sentence_length": round(avg_sentence_length, 2),
        "avg_syllables_per_word": round(avg_syllables_per_word, 2),
        "total_sentences": total_sentences,
        "total_words": total_words,
        "total_syllables": total_syllables
    }


def count_syllables(word: str) -> int:
    """
    Count syllables in a word.
    
    Args:
        word: Word to count syllables for
        
    Returns:
        Number of syllables
    """
    if not word:
        return 0
    
    word = word.lower()
    vowels = 'aeiouy'
    syllable_count = 0
    prev_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            syllable_count += 1
        prev_was_vowel = is_vowel
    
    # Handle silent 'e'
    if word.endswith('e') and syllable_count > 1:
        syllable_count -= 1
    
    # Minimum 1 syllable
    return max(1, syllable_count)


def extract_writing_patterns(text: str) -> Dict[str, Any]:
    """
    Extract writing patterns and style characteristics.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary of writing patterns
    """
    if not text:
        return {}
    
    # Sentence patterns
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Word patterns
    words = text.split()
    words = [w.strip(string.punctuation) for w in words if w.strip(string.punctuation)]
    
    # Character patterns
    chars = list(text)
    
    # Calculate patterns
    patterns = {
        "sentence_patterns": {
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "sentence_length_variance": calculate_variance([len(s.split()) for s in sentences]),
            "short_sentences_ratio": sum(1 for s in sentences if len(s.split()) <= 10) / len(sentences) if sentences else 0,
            "long_sentences_ratio": sum(1 for s in sentences if len(s.split()) > 20) / len(sentences) if sentences else 0
        },
        "word_patterns": {
            "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
            "word_length_variance": calculate_variance([len(w) for w in words]),
            "unique_words_ratio": len(set(words)) / len(words) if words else 0,
            "repeated_words_ratio": (len(words) - len(set(words))) / len(words) if words else 0
        },
        "punctuation_patterns": {
            "comma_frequency": text.count(',') / len(words) if words else 0,
            "semicolon_frequency": text.count(';') / len(words) if words else 0,
            "colon_frequency": text.count(':') / len(words) if words else 0,
            "dash_frequency": text.count('-') / len(words) if words else 0,
            "parentheses_frequency": text.count('(') / len(words) if words else 0,
            "quotation_frequency": text.count('"') / len(words) if words else 0
        },
        "capitalization_patterns": {
            "uppercase_ratio": sum(1 for c in chars if c.isupper()) / len(chars) if chars else 0,
            "title_case_ratio": sum(1 for w in words if w.istitle()) / len(words) if words else 0
        }
    }
    
    # Round numeric values
    for category in patterns:
        for key, value in patterns[category].items():
            if isinstance(value, float):
                patterns[category][key] = round(value, 4)
    
    return patterns


def calculate_variance(values: List[float]) -> float:
    """
    Calculate variance of a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Variance
    """
    if not values:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return round(variance, 4)


def extract_vocabulary_metrics(text: str) -> Dict[str, Any]:
    """
    Extract vocabulary and language complexity metrics.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary of vocabulary metrics
    """
    if not text:
        return {}
    
    words = text.split()
    words = [w.strip(string.punctuation).lower() for w in words if w.strip(string.punctuation)]
    
    if not words:
        return {}
    
    # Word frequency analysis
    word_freq = Counter(words)
    
    # Vocabulary metrics
    unique_words = len(word_freq)
    total_words = len(words)
    
    # Most common words
    most_common = word_freq.most_common(10)
    
    # Word length distribution
    word_lengths = [len(w) for w in words]
    length_distribution = Counter(word_lengths)
    
    # Complex words (more than 6 characters)
    complex_words = [w for w in words if len(w) > 6]
    complex_word_ratio = len(complex_words) / total_words
    
    return {
        "vocabulary_richness": unique_words / total_words,
        "total_unique_words": unique_words,
        "total_words": total_words,
        "complex_word_ratio": round(complex_word_ratio, 4),
        "most_common_words": most_common,
        "avg_word_length": round(sum(word_lengths) / len(word_lengths), 2),
        "word_length_distribution": dict(length_distribution)
    }


def extract_style_signatures(text: str) -> Dict[str, Any]:
    """
    Extract style signatures that can be used for comparison.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary of style signatures
    """
    if not text:
        return {}
    
    # Get all metrics
    readability = calculate_readability_metrics(text)
    patterns = extract_writing_patterns(text)
    vocabulary = extract_vocabulary_metrics(text)
    
    # Create style signature
    signature = {
        "readability_profile": {
            "flesch_reading_ease": readability.get("flesch_reading_ease", 0),
            "flesch_kincaid_grade": readability.get("flesch_kincaid_grade", 0),
            "avg_sentence_length": readability.get("avg_sentence_length", 0)
        },
        "writing_style": {
            "sentence_variety": patterns.get("sentence_patterns", {}).get("sentence_length_variance", 0),
            "punctuation_style": {
                "comma_usage": patterns.get("punctuation_patterns", {}).get("comma_frequency", 0),
                "semicolon_usage": patterns.get("punctuation_patterns", {}).get("semicolon_frequency", 0),
                "dash_usage": patterns.get("punctuation_patterns", {}).get("dash_frequency", 0)
            },
            "vocabulary_complexity": vocabulary.get("complex_word_ratio", 0),
            "vocabulary_richness": vocabulary.get("vocabulary_richness", 0)
        },
        "text_characteristics": {
            "avg_word_length": patterns.get("word_patterns", {}).get("avg_word_length", 0),
            "unique_word_ratio": patterns.get("word_patterns", {}).get("unique_words_ratio", 0),
            "capitalization_style": patterns.get("capitalization_patterns", {}).get("uppercase_ratio", 0)
        }
    }
    
    return signature
