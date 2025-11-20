# planner/features/ai_helper.py (Complete Corrected File)

import os
import json
import re
from typing import List, Dict
import openai
from django.conf import settings
from datetime import datetime

# Set OpenAI API key from settings
# Using getattr is safer in Django settings context
openai.api_key = getattr(settings, 'OPENAI_API_KEY', None)

def _clean_and_load_json(response_content: str) -> List[Dict]:
    """Helper function to clean non-JSON text (like markdown) and load JSON."""
    
    # 1. Strip markdown code fences (```json ... ```)
    cleaned_content = re.sub(r'```json|```', '', response_content, flags=re.DOTALL).strip()
    
    # 2. Attempt to parse JSON
    try:
        return json.loads(cleaned_content)
    except json.JSONDecodeError as e:
        # Fallback to simple list/dict structure if parsing fails
        print(f"JSON Decode Error in LLM response: {e}")
        return []

def external_summarize(text: str, max_tokens: int = 200) -> str:
    """Summarize text using OpenAI API, falling back to local method on failure."""
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
        print(f"OpenAI API error during summarization: {e}")
        from .summarizer import summarize_text
        return summarize_text(text, max_sentences=7)

def generate_quiz_questions(text: str, num_questions: int = 5) -> List[Dict]:
    """
    Generate quiz questions using OpenAI API.
    Returns list of dicts: {"question": str, "options": [str], "answer": str} (Correct format for views.py)
    """
    if not openai.api_key:
        # Fallback to the local generator (assuming you named it quiz_generator or used ai_helper for mock)
        # Note: If you don't have a file named quiz_generator.py, change this line to your mock file
        from .ai_helper_mock import generate_quiz_questions as generate_quiz_from_text 
        return generate_quiz_from_text(text, num_questions)

    try:
        prompt = (f"Generate {num_questions} multiple-choice questions based on the following text. "
                  f"Format the output strictly as a JSON list of objects. Each object must have keys: "
                  f"question (str), options (list of 4 strings), and answer (the option letter, e.g., 'A' or 'B').\n\nText:\n{text}")
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an educational quiz generator. Output only the requested JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        quiz_data = _clean_and_load_json(response.choices[0].message.content)
        
        # Ensure the final answer is a single letter (A, B, C, D) for Django model consistency
        for q in quiz_data:
            if 'answer' in q and isinstance(q['answer'], str):
                q['answer'] = q['answer'].upper().strip()[:1]
        
        return quiz_data
        
    except Exception as e:
        print(f"OpenAI API error during quiz generation: {e}")
        # Fallback to the local generator
        from .ai_helper_mock import generate_quiz_questions as generate_quiz_from_text 
        return generate_quiz_from_text(text, num_questions)


def generate_study_plan_ai(subjects: List[Dict], start_date: str, exam_date: str) -> List[Dict]:
    """
    Generate study plan using OpenAI API.
    Returns list of dicts: {"date": str, "subject_name": str, "hours": float, "topics": str} (Correct format for views.py)
    """
    if not openai.api_key:
        from .study_planner import generate_study_plan
        start = datetime.fromisoformat(start_date)
        exam = datetime.fromisoformat(exam_date)
        return generate_study_plan(subjects, start, exam)
    
    try:
        subjects_str = "\n".join([f"- {s['name']} (weightage: {s.get('weightage', 1)})" for s in subjects])
        prompt = (f"Create a detailed study plan from {start_date} to {exam_date} for the following subjects:\n{subjects_str}\n\n"
                  f"Provide a daily plan in JSON format: list of objects. Each object must have keys: "
                  f"date (YYYY-MM-DD), subject_name (the subject's name), hours (float), and topics (brief description of topics to cover).")
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a study planner assistant. Output only the requested JSON list."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.5
        )
        
        plan_data = _clean_and_load_json(response.choices[0].message.content)
        
        # CRUCIAL: Rename 'subject' key to 'subject_name' for Django view consistency
        for item in plan_data:
            if 'subject' in item:
                item['subject_name'] = item.pop('subject')
        
        return plan_data
        
    except Exception as e:
        print(f"OpenAI API error during plan generation: {e}")
        from .study_planner import generate_study_plan
        start = datetime.fromisoformat(start_date)
        exam = datetime.fromisoformat(exam_date)
        return generate_study_plan(subjects, start, exam)