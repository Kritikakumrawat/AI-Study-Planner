# planner/features/summarizer.py (Complete Corrected File)

from typing import List

def summarize_text(text: str, max_sentences: int = 5) -> str:
    """
    Lightweight summarizer: returns first N sentences as a summary.
    This is the local fallback implementation, formatted for better readability in notes.
    """
    if not text:
        return ""
    
    # Crude split on periods, accounting for newlines and multiple spaces
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    
    # Join the top sentences with newlines for cleaner display in the notes field
    summary = "\n- ".join(sentences[:max_sentences])
    
    # Add a header to indicate this is a local fallback
    return "--- Local Summarization Fallback ---\n\n- " + summary