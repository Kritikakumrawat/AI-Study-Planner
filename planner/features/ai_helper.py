import json
from pydantic import BaseModel, Field
from typing import List

# --- Define the Models (Note and Subject) ---

# This defines the data structure for the subject line
# ai_helper.py (CORRECTED CODE)
# This defines the data structure for the subject line
class SubjectLineModel(BaseModel):
    """Subject line for a note."""
    subject_line: str = Field(description="A concise, descriptive subject line for the note.")

# This defines the data structure for the main note content
class Note(BaseModel):
    """A user note containing subject and content."""
    subject: str = Field(description="The subject of the note. Should be concise.")
    content: str = Field(description="The main body or content of the note.")

# --- Define the AI Helper Class ---

class AiHelper:
    """
    A class to encapsulate functions that an AI can use, 
    such as creating notes and generating content (summary, quiz, plan).
    """
    
    def __init__(self, notes_storage_file="notes.json"):
        """Initialize the AiHelper with a storage file."""
        self.notes_storage_file = notes_storage_file
        # print(f"AiHelper initialized. Notes will be stored in: {self.notes_storage_file}")
    
    # --- CRUD Methods for Notes ---

    def create_note(self, note: Note) -> str:
        """
        Creates and stores a new note based on the provided Note object.
        (This method remains unchanged, using the note data structure)
        """
        try:
            new_note = {
                "subject": note.subject,
                "content": note.content
            }
            
            # 1. Load existing notes
            notes = self._load_notes()
            
            # 2. Add the new note
            notes.append(new_note)
            
            # 3. Save all notes
            self._save_notes(notes)
            
            return f"Note successfully created with Subject: '{new_note['subject']}' and Content: '{new_note['content'][:50]}...'"
            
        except Exception as e:
            return f"Error creating note: {str(e)}"

    def _load_notes(self) -> List[dict]:
        """Loads notes from the JSON storage file."""
        try:
            with open(self.notes_storage_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            # print(f"Warning: '{self.notes_storage_file}' is corrupted. Starting with an empty list.")
            return []

    def _save_notes(self, notes: List[dict]):
        """Saves the current list of notes to the JSON storage file."""
        with open(self.notes_storage_file, 'w') as f:
            json.dump(notes, f, indent=4)

    def get_notes_summary(self) -> str:
        """Retrieves a summary of all stored notes."""
        notes = self._load_notes()
        if not notes:
            return "No notes currently stored."
            
        summary = "Current Notes Summary:\n"
        for i, note in enumerate(notes, 1):
            summary += f"{i}. Subject: {note['subject']}\n"
            
        return summary
    
    # --- AI Generation Methods (Needed by views.py) ---
    # These are the functions your views.py expects to call via the AiHelper instance.

    def external_summarize(self, text: str) -> str:
        """
        Generates a summary/notes from the provided text using an AI service.
        *** NOTE: You must integrate your actual AI API calls here. ***
        """
        # --- PLACEHOLDER LOGIC ---
        if not text or len(text) < 50:
            return "Generated Notes: Not enough input text to create a detailed summary."
        
        summary_text = f"Comprehensive AI-Generated Notes on the provided material:\n\n{text[:200]}...\n\n(Full AI logic integration required here.)"
        # --- END PLACEHOLDER LOGIC ---
        return summary_text

    def generate_quiz_questions(self, text: str, num_questions: int = 5) -> List[dict]:
        """
        Generates a list of quiz questions from the text using an AI service.
        *** NOTE: You must integrate your actual AI API calls here. ***
        """
        # --- PLACEHOLDER LOGIC (Returns mock data structure) ---
        if not text:
            return []
            
        return [
            {'question': 'Mock Q1: What color is the sky?', 'options': ['Red', 'Blue', 'Green', 'Yellow'], 'answer': 'B'},
            {'question': 'Mock Q2: What is the capital of France?', 'options': ['Berlin', 'Paris', 'Madrid', 'Rome'], 'answer': 'B'},
            {'question': 'Mock Q3: What is 2 + 2?', 'options': ['3', '4', '5', '6'], 'answer': 'B'},
            {'question': 'Mock Q4: What is the primary function of Python?', 'options': ['Eating', 'Sleeping', 'Programming', 'Singing'], 'answer': 'C'},
            {'question': 'Mock Q5: AI Helper created this question. True or False?', 'options': ['True', 'False'], 'answer': 'A'},
        ]
        # --- END PLACEHOLDER LOGIC ---

    def generate_study_plan_ai(self, subjects: List[dict], start_date: str, end_date: str) -> List[dict]:
        """
        Generates a study plan based on subjects, start date, and end date.
        *** NOTE: You must integrate your actual AI API calls here. ***
        """
        # --- PLACEHOLDER LOGIC (Returns mock data structure) ---
        if not subjects:
            return []
        
        mock_subject_name = subjects[0]['name']
        
        # Simple two-day plan for the first subject
        return [
            {'subject_name': mock_subject_name, 'date': start_date, 'topics': f'AI Plan: Intro to {mock_subject_name} (2 hours)', 'hours': 2},
            {'subject_name': mock_subject_name, 'date': end_date, 'topics': f'AI Plan: Review for {mock_subject_name} exam (3 hours)', 'hours': 3},
        ]
        # --- END PLACEHOLDER LOGIC ---

# --- Example of How to Use the Class (Optional) ---
if __name__ == '__main__':
    helper = AiHelper()
    
    # 1. Test Note Creation (Existing logic)
    sample_note = Note(
        subject="Test Note",
        content="This is a test content for note creation."
    )
    result = helper.create_note(sample_note)
    print("\n--- Result of create_note ---")
    print(result)
    
    # 2. Test Summarize
    test_summary = helper.external_summarize("A long piece of text about something important. This text needs to be summarized by the AI.")
    print("\n--- Result of external_summarize ---")
    print(test_summary)
    
    # Note: This will create a file named 'notes.json' in the same directory.