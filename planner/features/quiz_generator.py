# planner/features/quiz_generator.py
import random
from typing import List, Dict

def generate_quiz_from_text(text: str, num_questions: int = 5) -> List[Dict]:
    """
    Return a list of question dicts:
    { "question": str, "options": [str], "answer": str }
    This is a simple algorithmic generator: it picks sentences to form 'questions'.
    """
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 20]
    if not sentences:
        # Fallback quiz if no sentences
        return [
            {
                "question": "What is the capital of France?",
                "options": ["Paris", "London", "Berlin", "Madrid"],
                "answer": "Paris"
            },
            {
                "question": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "answer": "4"
            }
        ][:num_questions]
    quiz = []
    # take up to num_questions distinct sentences
    chosen = random.sample(sentences, min(len(sentences), num_questions))
    for qsent in chosen:
        # create 3 distractors from other sentences if possible
        distractors = random.sample([s for s in sentences if s != qsent], min(3, max(0, len(sentences)-1)))
        if len(distractors) < 3:
            # Add dummy options if not enough
            distractors.extend(["Option A", "Option B", "Option C"][:3-len(distractors)])
        options = distractors + [qsent]
        random.shuffle(options)
        quiz.append({
            "question": f"Explain in short: {qsent[:70]}...",
            "options": options,
            "answer": qsent
        })
    return quiz
