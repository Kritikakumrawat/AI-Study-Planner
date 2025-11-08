# planner/features/ai_helper.py
import os
from typing import Optional, List, Dict
import openai
from django.conf import settings

# Set OpenAI API key from settings
openai.api_key = getattr(settings, 'OPENAI_API_KEY', None)

def external_summarize(text: str, max_tokens: int = 200) -> str:
    """
    Summarize text using OpenAI API.
    Falls back to local summarizer if API key is not set or error occurs.
    """
    if not openai.api_key:
        from .summarizer import summarize_text
        return summarize_text(text, max_sentences=7)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes educational content."},
                {"role": "user", "content": f"Summarize the following text in about {max_tokens} tokens:\n\n{text}"}
            ],
            max_tokens=max_tokens,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        from .summarizer import summarize_text
        return summarize_text(text, max_sentences=7)

def generate_quiz_questions(text: str, num_questions: int = 5) -> List[Dict]:
    """
    Generate quiz questions using OpenAI API.
    Returns list of dicts: {"question": str, "options": [str], "answer": str}
    Falls back to algorithmic generator if API key not set or error.
    """
    if not openai.api_key:
        from .quiz_generator import generate_quiz_from_text
        return generate_quiz_from_text(text, num_questions)
    try:
        prompt = f"Generate {num_questions} multiple-choice questions based on the following text. Each question should have 4 options (A, B, C, D) and indicate the correct answer. Format as JSON list of objects with keys: question, options (list of 4 strings), answer (the correct option text).\n\nText:\n{text}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational quiz generator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        # Parse the response (assuming JSON format)
        import json
        quiz_data = json.loads(response.choices[0].message.content.strip())
        return quiz_data
    except Exception as e:
        print(f"OpenAI API error: {e}")
        from .quiz_generator import generate_quiz_from_text
        return generate_quiz_from_text(text, num_questions)

def generate_study_plan_ai(subjects: List[Dict], start_date: str, exam_date: str) -> List[Dict]:
    """
    Generate study plan using OpenAI API.
    subjects: list of dict {"name": str, "weightage": int}
    start_date, exam_date: strings in YYYY-MM-DD
    Returns list of dicts: {"date": str, "subject": str, "hours": float, "topics": str}
    Falls back to algorithmic planner if API key not set or error.
    """
    if not openai.api_key:
        from .study_planner import generate_study_plan
        from datetime import datetime
        start = datetime.fromisoformat(start_date)
        exam = datetime.fromisoformat(exam_date)
        return generate_study_plan(subjects, start, exam)
    try:
        subjects_str = "\n".join([f"- {s['name']} (weightage: {s.get('weightage', 1)})" for s in subjects])
        prompt = f"Create a study plan from {start_date} to {exam_date} for the following subjects:\n{subjects_str}\n\nProvide a daily plan in JSON format: list of objects with keys: date (YYYY-MM-DD), subject, hours (float), topics (brief description)."
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a study planner assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.5
        )
        import json
        plan_data = json.loads(response.choices[0].message.content.strip())
        return plan_data
    except Exception as e:
        print(f"OpenAI API error: {e}")
        from .study_planner import generate_study_plan
        from datetime import datetime
        start = datetime.fromisoformat(start_date)
        exam = datetime.fromisoformat(exam_date)
        return generate_study_plan(subjects, start, exam)
