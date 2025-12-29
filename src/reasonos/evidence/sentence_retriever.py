"""Sentence-based evidence retrieval for ReasonOS.

Provides deterministic keyword-overlap retrieval without embeddings.
"""

from typing import Any

from ..utils.text import split_sentences, tokenize


def retrieve_evidence(
    paragraph: str,
    document_text: str,
    k: int = 3,
) -> list[dict[str, Any]]:
    """
    Retrieve top-k evidence sentences from document based on keyword overlap.

    Uses deterministic scoring: count of overlapping tokens between query
    and each document sentence. Ties are broken by sentence order (earlier first).

    Args:
        paragraph: The query paragraph containing the claim.
        document_text: The full document text to search.
        k: Maximum number of evidence sentences to return.

    Returns:
        A list of evidence dictionaries, each containing:
            - content: The sentence text
            - relevance_score: Overlap score normalized to [0, 1]
            - sentence_index: Original position in document
    """
    if not paragraph or not document_text:
        return []

    # Tokenize query
    query_tokens = set(tokenize(paragraph))
    if not query_tokens:
        return []

    # Split document into sentences
    sentences = split_sentences(document_text)
    if not sentences:
        return []

    # Score each sentence by token overlap
    scored_sentences = []
    for idx, sentence in enumerate(sentences):
        sentence_tokens = set(tokenize(sentence))
        overlap = len(query_tokens & sentence_tokens)
        # Normalize score to [0, 1]
        relevance_score = overlap / max(1, len(query_tokens))
        scored_sentences.append({
            "content": sentence,
            "relevance_score": round(relevance_score, 3),
            "sentence_index": idx,
            "overlap_count": overlap,
        })

    # Sort by overlap count descending, then by sentence index ascending for ties
    scored_sentences.sort(key=lambda x: (-x["overlap_count"], x["sentence_index"]))

    # Take top k and remove internal scoring field
    results = []
    for item in scored_sentences[:k]:
        results.append({
            "content": item["content"],
            "relevance_score": item["relevance_score"],
            "sentence_index": item["sentence_index"],
        })

    return results
