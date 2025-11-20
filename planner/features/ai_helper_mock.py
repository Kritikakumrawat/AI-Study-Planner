# planner/features/ai_helper_mock.py
# Mock implementation for quiz generation when API is unavailable

from typing import List, Dict
import random

def generate_quiz_questions_mock(text: str, num_questions: int = 5) -> List[Dict]:
    """Mocks AI generation of quiz questions based on input text."""
    
    subject_name = text.split("for")[-1].strip().split(".")[0].strip()
    
    mock_quizzes = [
        {
            "question": f"MOCK Q1: What is the primary focus area of {subject_name}?",
            "options": ["Core Concepts", "Advanced Theory", "Local Mock Testing", "Historical Dates"],
            "answer": "C" 
        },
        {
            "question": f"MOCK Q2: Which letter represents the best answer in a mock test?",
            "options": ["A", "B", "C", "D"],
            "answer": "B"
        },
        {
            "question": f"MOCK Q3: The current date is close to the year:",
            "options": ["2022", "2023", "2024", "2025"],
            "answer": "D"
        }
    ]
    
    # Return up to num_questions from the mock list
    return mock_quizzes[:num_questions]