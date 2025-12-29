"""Text processing utilities for ReasonOS."""

import re


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.

    Replaces multiple whitespace characters with single spaces and strips
    leading/trailing whitespace.

    Args:
        text: The input text to normalize.

    Returns:
        Text with normalized whitespace.
    """
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    """
    Split text into sentences using punctuation delimiters.

    Uses a simple deterministic approach splitting on . ! ? followed by
    whitespace or end of string.

    Args:
        text: The input text to split.

    Returns:
        A list of sentence strings, each stripped of leading/trailing whitespace.
    """
    # Split on sentence-ending punctuation followed by space or end
    pattern = r"(?<=[.!?])\s+"
    sentences = re.split(pattern, text)

    # Clean up and filter empty strings
    result = []
    for sentence in sentences:
        cleaned = normalize_whitespace(sentence)
        if cleaned:
            result.append(cleaned)

    return result


def extract_percent_value(text: str) -> float | None:
    """
    Extract the first percentage value from text.

    Matches patterns like "15 percent", "14.8 percent", "15%".

    Args:
        text: The text to search for percentage values.

    Returns:
        The numeric value as a float, or None if no match found.
    """
    # Match number followed by "percent" or "%"
    pattern = r"(\d+(?:\.\d+)?)\s*(?:percent|%)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase words.

    Removes punctuation and splits on whitespace.

    Args:
        text: The text to tokenize.

    Returns:
        A list of lowercase word tokens.
    """
    # Remove punctuation and split
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return cleaned.split()
