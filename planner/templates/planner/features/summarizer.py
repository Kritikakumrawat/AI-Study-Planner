# planner/features/summarizer.py
from typing import List

def summarize_text(text: str, max_sentences: int = 5) -> str:
    """
    Lightweight summarizer: returns first N sentences as a summary.
    Replace this with LLM call later (ai_helper.wrap_summary).
    """
    if not text:
        return ""
    # crude split on periods for now
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    return ". ".join(sentences[:max_sentences]) + ("" if len(sentences) <= max_sentences else ".")
