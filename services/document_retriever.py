import re

from models import DocumentChunk, HRPolicy


def tokenize(text):
    """Convert text into searchable words."""

    return set(
        re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    )


def retrieve_relevant_chunks(question, top_k=5):

    """
    Retrieve policy document sections relevant
    to an employee's question.
    """

    question_words = tokenize(question)

    if not question_words:
        return []

    chunks = (
        DocumentChunk.query
        .join(HRPolicy)
        .filter(HRPolicy.is_active.is_(True))
        .all()
    )

    scored_chunks = []

    for chunk in chunks:

        chunk_words = tokenize(chunk.content)

        matching_words = question_words.intersection(chunk_words)

        if not matching_words:
            continue

        score = len(matching_words) / len(question_words)

        scored_chunks.append({
            "content": chunk.content,
            "policy_title": chunk.policy.title,
            "score": score
        })

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return scored_chunks[:top_k]