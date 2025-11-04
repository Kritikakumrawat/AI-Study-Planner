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
        return []
    quiz = []
    # take up to num_questions distinct sentences
    chosen = random.sample(sentences, min(len(sentences), num_questions))
    for qsent in chosen:
        # create 3 distractors from other sentences if possible
        distractors = random.sample([s for s in sentences if s != qsent], min(3, max(0, len(sentences)-1)))
        options = distractors + [qsent]
        random.shuffle(options)
        quiz.append({
            "question": f"Explain in short: {qsent[:70]}...",
            "options": options,
            "answer": qsent
        })
    return quiz
