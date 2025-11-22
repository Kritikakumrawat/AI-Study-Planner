import json
import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from openai import OpenAI
from dotenv import load_dotenv 

# --- Load Environment Variables ---
load_dotenv()
# ----------------------------------

# --- Define the Models (Note, Subject, Quiz, and Plan Structures) ---

class SubjectLineModel(BaseModel):
    """Subject line for a note."""
    subject_line: str = Field(description="A concise, descriptive subject line for the note.")

class Note(BaseModel):
    """A user note containing subject and content."""
    subject: str = Field(description="The subject of the note. Should be concise.")
    content: str = Field(description="The main body or content of the note.")

class QuizQuestionModel(BaseModel):
    question: str = Field(description="The quiz question text.")
    options: List[str] = Field(description="A list of 4 possible answers.")
    answer: str = Field(description="The correct answer key (e.g., 'A', 'B', 'C', or 'D').")

class QuizModel(BaseModel):
    questions: List[QuizQuestionModel]

class StudyTaskModel(BaseModel):
    subject_name: str = Field(description="The name of the subject for this task.")
    date: str = Field(description="The date of the study task in YYYY-MM-DD format.")
    topics: str = Field(description="A brief description of the topics to be covered.")
    hours: int = Field(description="The estimated hours for this task.")

class StudyPlanModel(BaseModel):
    plan: List[StudyTaskModel]


# --- Define the AI Helper Class ---

class AiHelper:
    """
    A class to encapsulate functions that an AI can use, 
    integrated with the OpenAI API.
    """
    
    def __init__(self, notes_storage_file="notes.json"):
        """Initialize the AiHelper and configure the OpenAI client."""
        self.notes_storage_file = notes_storage_file
        
        # --- FIXED: Client Initialization (Will now find the key) ---
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo-1106"
        # -----------------------------------
    
    # --- Utility methods (CRUD/load/save methods) ---
    def _load_notes(self) -> List[dict]:
        try:
            with open(self.notes_storage_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_notes(self, notes: List[dict]):
        with open(self.notes_storage_file, 'w') as f:
            json.dump(notes, f, indent=4)
            
    def create_note(self, note: Note) -> str:
        try:
            new_note = {"subject": note.subject, "content": note.content}
            notes = self._load_notes()
            notes.append(new_note)
            self._save_notes(notes) # Corrected utility method call
            return f"Note successfully created with Subject: '{new_note['subject']}'..."
        except Exception as e:
            return f"Error creating note: {str(e)}"
            
    def get_notes_summary(self) -> str:
        notes = self._load_notes()
        if not notes: return "No notes currently stored."
        summary = "Current Notes Summary:\n"
        for i, note in enumerate(notes, 1): summary += f"{i}. Subject: {note['subject']}\n"
        return summary
    
    # --- AI Generation Methods (Now with API Calls) ---

    def external_summarize(self, text: str) -> str:
        """Generates a detailed summary/notes from the provided text using the AI service."""
        
        prompt = (
            f"Please generate comprehensive study notes and a detailed summary of the following material. "
            f"Focus on key concepts, definitions, and essential facts. The source material is:\n\n{text}"
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert academic assistant who creates clear, structured study notes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content

    def generate_quiz_questions(self, text: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """Generates a list of quiz questions from the text using structured JSON output."""
        
        prompt = (
            f"Generate exactly {num_questions} multiple-choice quiz questions based on the following material. "
            f"Each question must have 4 options, and the correct answer must be one of 'A', 'B', 'C', or 'D'. "
            f"The source material is:\n\n{text}"
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a quiz master. Output a JSON object that strictly adheres to the schema for QuizModel."},
                {"role": "user", "content": prompt}
            ],
            response_model=QuizModel,
            temperature=0.5,
        )
        return response.questions

    def generate_study_plan_ai(self, subjects: List[dict], start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Generates a multi-subject study plan using the AI service with JSON output."""
        
        subjects_str = json.dumps(subjects)
        
        prompt = (
            f"Create a detailed study plan starting on {start_date} and ending on {end_date}. "
            f"The plan must include daily or multi-day tasks for each subject listed in the JSON below. "
            f"Allocate study hours (1-4 hours per day) based on the subject's 'weightage' (0-100). "
            f"The output must be a list of tasks in YYYY-MM-DD format. Subjects: {subjects_str}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a study planning expert. Output a JSON object that strictly adheres to the schema for StudyPlanModel."},
                {"role": "user", "content": prompt}
            ],
            response_model=StudyPlanModel,
            temperature=0.7,
        )
        return response.plan