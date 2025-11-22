import unittest
from unittest.mock import patch, MagicMock
from planner.features.ai_helper import AiHelper, Note, QuizModel, StudyPlanModel
import json

class TestAiHelper(unittest.TestCase):

    def setUp(self):
        self.ai_helper = AiHelper(notes_storage_file="test_notes.json")

    def test_create_note_and_summary(self):
        note = Note(subject="Math", content="Algebra study")
        create_msg = self.ai_helper.create_note(note)
        self.assertIn("Note successfully created", create_msg)
        summary = self.ai_helper.get_notes_summary()
        self.assertIn("Math", summary)

    @patch('planner.features.ai_helper.OpenAI')
    def test_external_summarize(self, MockOpenAI):
        mock_client = MockOpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summary of text"
        mock_client.chat.completions.create.return_value = mock_response
        
        self.ai_helper.client = mock_client
        result = self.ai_helper.external_summarize("Some text")
        self.assertEqual(result, "Summary of text")

    @patch('planner.features.ai_helper.OpenAI')
    def test_generate_quiz_questions(self, MockOpenAI):
        mock_client = MockOpenAI.return_value
        mock_response = MagicMock()
        sample_quiz_json = {
            "questions": [
                {
                    "question": "What is 2+2?",
                    "options": ["1", "2", "3", "4"],
                    "answer": "D"
                }
            ]
        }
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(sample_quiz_json)
        mock_client.chat.completions.create.return_value = mock_response
        
        self.ai_helper.client = mock_client
        questions = self.ai_helper.generate_quiz_questions("Math text", num_questions=1)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question, "What is 2+2?")
        self.assertEqual(questions[0].answer, "D")

    @patch('planner.features.ai_helper.OpenAI')
    def test_generate_study_plan_ai(self, MockOpenAI):
        mock_client = MockOpenAI.return_value
        mock_response = MagicMock()
        sample_plan_json = {
            "plan": [
                {
                    "subject_name": "Math",
                    "date": "2023-01-01",
                    "topics": "Algebra",
                    "hours": 2
                }
            ]
        }
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(sample_plan_json)
        mock_client.chat.completions.create.return_value = mock_response
        
        self.ai_helper.client = mock_client
        subjects = [{"name": "Math", "weightage": 50}]
        plan = self.ai_helper.generate_study_plan_ai(subjects, "2023-01-01", "2023-01-07")
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].subject_name, "Math")
        self.assertEqual(plan[0].topics, "Algebra")

if __name__ == '__main__':
    unittest.main()
