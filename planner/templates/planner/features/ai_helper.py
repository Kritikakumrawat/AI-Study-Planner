# planner/features/ai_helper.py
import os
from typing import Optional, List, Dict
import openai

# Set up OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def external_summarize(text: str, max_tokens: int = 200) -> str:
    """
    Summarize text using OpenAI GPT.
    """
    if not text.strip():
        return ""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text concisely."},
                {"role": "user", "content": f"Summarize the following text in about {max_tokens} tokens or less:\n\n{text}"}
            ],
            max_tokens=max_tokens,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in external_summarize: {e}")
        # Fallback to local summarizer
        from .summarizer import summarize_text
        return summarize_text(text, max_sentences=7)

def generate_quiz_ai(text: str, num_questions: int = 5) -> List[Dict]:
    """
    Generate quiz questions using OpenAI.
    Returns list of dicts: {"question": str, "options": [str], "answer": str}
    """
    if not text.strip():
        return []
    try:
        prompt = f"Generate {num_questions} multiple-choice questions based on the following text. Each question should have 4 options (A, B, C, D) and indicate the correct answer. Format as JSON list of objects with keys: question, options (list), answer (the correct option text).\n\nText:\n{text}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a quiz generator. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        import json
        quiz_data = json.loads(response.choices[0].message.content.strip())
        return quiz_data[:num_questions]
    except Exception as e:
        print(f"Error in generate_quiz_ai: {e}")
        # Fallback to local generator
        from .quiz_generator import generate_quiz_from_text
        return generate_quiz_from_text(text, num_questions)

def chatbot_response(message: str, context: str = "") -> str:
    """
    Generate chatbot response using OpenAI.
    Context can be study-related info.
    """
    try:
        system_prompt = "You are a helpful AI study assistant. Help with study planning, notes, quizzes, and general questions. Keep responses concise."
        if context:
            system_prompt += f" Context: {context}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in chatbot_response: {e}")
        return "Sorry, I'm having trouble responding right now. Please try again later."
