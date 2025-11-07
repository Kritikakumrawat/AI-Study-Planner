# TODO: Integrate OpenAI and Add Chatbot to AI Study Planner

## Steps to Complete

- [x] Add 'openai' to planner/templates/planner/features/requirements.txt
- [x] Implement OpenAI client in planner/templates/planner/features/ai_helper.py (functions: external_summarize, generate_quiz_ai, chatbot_response)
- [x] Update planner/templates/planner/features/summarizer.py to use ai_helper.external_summarize
- [x] Enhance planner/templates/planner/features/quiz_generator.py with AI-generated questions using ai_helper
- [x] Modify planner/views.py generate_notes to use AI for content generation
- [x] Add Chat model to planner/models.py for conversation history
- [x] Add chat_view to planner/views.py for handling chatbot interactions
- [x] Create planner/templates/planner/chat.html template for chatbot interface
- [x] Update planner/urls.py to include chatbot URL
- [x] Run migrations for new Chat model
- [x] Install dependencies from requirements.txt
- [ ] Set up OPENAI_API_KEY environment variable
- [ ] Test the chatbot and AI features
