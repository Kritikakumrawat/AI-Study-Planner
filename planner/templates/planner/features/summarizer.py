# planner/features/summarizer.py
from typing import List

def summarize_text(text: str, max_sentences: int = 5) -> str:
    """
    Summarize text using AI (OpenAI) if available, else fallback to lightweight method.
    """
    if not text:
        return ""
    # Try AI summarization first
    from .ai_helper import external_summarize
    ai_summary = external_summarize(text, max_tokens=200)
    if ai_summary and ai_summary != text[:200]:  # Check if it's a real summary
        return ai_summary
    # Fallback to local method
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    return ". ".join(sentences[:max_sentences]) + ("" if len(sentences) <= max_sentences else ".")
