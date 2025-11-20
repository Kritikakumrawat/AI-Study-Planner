import random

def generate_quiz_questions_mock(text: str, num_questions: int = 5) -> list:
    """
    Mock function to generate quiz questions when OpenAI API is unavailable.
    Returns a list of dictionaries with keys: question, options, answer.
    """
    # Sample questions based on common study topics
    sample_questions = [
        {
            "question": "What is the capital of France?",
            "options": ["London", "Berlin", "Paris", "Madrid"],
            "answer": "C"
        },
        {
            "question": "Which planet is known as the Red Planet?",
            "options": ["Venus", "Mars", "Jupiter", "Saturn"],
            "answer": "B"
        },
        {
            "question": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "answer": "B"
        },
        {
            "question": "Who wrote Romeo and Juliet?",
            "options": ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"],
            "answer": "B"
        },
        {
            "question": "What is the largest ocean on Earth?",
            "options": ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "Pacific Ocean"],
            "answer": "D"
        },
        {
            "question": "What is the chemical symbol for water?",
            "options": ["H2O", "CO2", "O2", "NaCl"],
            "answer": "A"
        },
        {
            "question": "In which year did World War II end?",
            "options": ["1944", "1945", "1946", "1947"],
            "answer": "B"
        },
        {
            "question": "What is the square root of 16?",
            "options": ["2", "4", "8", "16"],
            "answer": "B"
        }
    ]

    # Randomly select the requested number of questions
    selected_questions = random.sample(sample_questions, min(num_questions, len(sample_questions)))

    return selected_questions
