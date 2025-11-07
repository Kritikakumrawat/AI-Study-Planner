# planner/features/quiz_generator.py
import random
from typing import List, Dict

def generate_quiz_from_text(text: str, num_questions: int = 5) -> List[Dict]:
    """
    Generate quiz using AI (OpenAI) if available, else fallback to algorithmic method.
    Returns list of dicts: { "question": str, "options": [str], "answer": str }
    """
    if not text.strip():
        return []
    # Try AI generation first
    from .ai_helper import generate_quiz_ai
    ai_quiz = generate_quiz_ai(text, num_questions)
    if ai_quiz:
        return ai_quiz
    # Fallback to local method
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 20]
    if not sentences:
        return []
    quiz = []
    chosen = random.sample(sentences, min(len(sentences), num_questions))
    for qsent in chosen:
        distractors = random.sample([s for s in sentences if s != qsent], min(3, max(0, len(sentences)-1)))
        options = distractors + [qsent]
        random.shuffle(options)
        quiz.append({
            "question": f"Explain in short: {qsent[:70]}...",
            "options": options,
            "answer": qsent
        })
    return quiz
