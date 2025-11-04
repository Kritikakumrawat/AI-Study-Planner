# planner/features/ai_helper.py
import os
from typing import Optional

# placeholder: if you integrate OpenAI or other LLMs, implement calls here.
def external_summarize(text: str, max_tokens: int = 200) -> str:
    """
    Placeholder function — implement LLM call here (OpenAI, Cohere etc.)
    For now it calls local summarizer in features.summarizer.
    """
    from .summarizer import summarize_text
    return summarize_text(text, max_sentences=7)
