from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Subject, StudyPlan, Notes, Chat
from .templates.planner.features.ai_helper import chatbot_response

# Home page
def home(request):
    return render(request, 'planner/home.html')

# List of all subjects
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'planner/subjects.html', {'subjects': subjects})

# Show study plan and notes for a subject
def study_plan_list(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    studyplans = StudyPlan.objects.filter(subject=subject)
    notes = Notes.objects.filter(subject=subject).order_by('-created_at')
    return render(request, 'planner/studyplan.html', {
        'subject': subject,
        'studyplans': studyplans,
        'notes': notes,
    })

# AI-generated Notes
def generate_notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    # Generate AI notes based on subject name or syllabus if available
    context = f"Subject: {subject.name}"
    if subject.syllabus_file:
        # Extract text from PDF if available
        from .templates.planner.features.pdf_reader import extract_text_from_pdf
        syllabus_text = extract_text_from_pdf(subject.syllabus_file.path)
        context += f"\nSyllabus: {syllabus_text[:1000]}"  # Limit to first 1000 chars
    generated_text = chatbot_response(f"Generate detailed study notes for {subject.name}.", context)
    Notes.objects.create(subject=subject, content=generated_text, ai_generated=True)
    notes = Notes.objects.filter(subject=subject)
    return render(request, 'planner/notes.html', {'subject': subject, 'notes': notes})

# Chatbot view
def chat_view(request):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            # Get context from subjects or recent notes
            context = "You are a study assistant. Help with planning, notes, quizzes."
            subjects = Subject.objects.all()
            if subjects:
                context += f" Subjects: {[s.name for s in subjects]}"
            ai_response = chatbot_response(user_message, context)
            Chat.objects.create(user_message=user_message, ai_response=ai_response)
        return redirect('chat')
    chats = Chat.objects.order_by('-created_at')[:20]  # Last 20 messages
    return render(request, 'planner/chat.html', {'chats': chats})
