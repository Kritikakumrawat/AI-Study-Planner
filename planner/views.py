from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages  # <-- Import messages
from .models import Subject, StudyPlan, Notes, Quiz
from .features.summarizer import summarize_text
from .features.ai_helper import generate_quiz_questions
from .features.study_planner import generate_study_plan
from .features.pdf_reader import extract_text_from_pdf
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)

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

# Display Notes for a subject
def notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    notes = Notes.objects.filter(subject=subject).order_by('-created_at')
    exam = subject.exams.first()  # Assuming one exam per subject
    exam_date = exam.exam_date if exam else None
    return render(request, 'planner/notes.html', {'subject': subject, 'notes': notes, 'exam_date': exam_date})

# Generate AI Notes
def generate_notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    # Check if syllabus file exists
    if not subject.syllabus_file:
        error_message = "No syllabus available for generating notes."
        logger.error(f"No syllabus file for subject {subject.name} (ID: {subject_id})")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})
        else:
            messages.error(request, error_message)
            return redirect('notes', subject_id=subject_id)

    text = ""
    try:
        text = extract_text_from_pdf(subject.syllabus_file.path)
    except Exception as e:
        logger.error(f"Failed to extract text from PDF for subject {subject.name} (ID: {subject_id}): {str(e)}")
        text = ""  # Treat as no text

    if not text:
        text = f"Sample content for {subject.name}. This is placeholder text for AI summarization."

    try:
        generated_text = summarize_text(text)
    except Exception as e:
        error_message = "AI failed to generate notes. Try again."
        logger.error(f"AI summarization failed for subject {subject.name} (ID: {subject_id}): {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})
        else:
            messages.error(request, error_message)
            return redirect('notes', subject_id=subject_id)

    note = Notes.objects.create(subject=subject, content=generated_text, ai_generated=True)

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,  # <-- **** KEY FIX 1 ****
                'content': note.content,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    else:
        return redirect('notes', subject_id=subject_id)

# Generate Quiz for a subject
def generate_quiz(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    text = ""
    if subject.syllabus_file:
        try:
            text = extract_text_from_pdf(subject.syllabus_file.path)
        except Exception as e:
            logger.error(f"Failed to extract PDF text for quiz (Subject: {subject.id}): {str(e)}")
            text = "" # Fallback to placeholder
            
    if not text:
        text = f"Sample content for {subject.name}. This is placeholder text for quiz generation."

    # --- **** KEY FIX 2 **** ---
    try:
        quiz_data = generate_quiz_questions(text, num_questions=5)
        
        # Optional: Clear old quizzes before adding new ones
        # Quiz.objects.filter(subject=subject).delete()

        for q in quiz_data:
            Quiz.objects.create(
                subject=subject,
                question=q['question'],
                option_a=q['options'][0] if len(q['options']) > 0 else "",
                option_b=q['options'][1] if len(q['options']) > 1 else "",
                option_c=q['options'][2] if len(q['options']) > 2 else "",
                option_d=q['options'][3] if len(q['options']) > 3 else "",
                correct_answer=q['answer']
            )
        
        messages.success(request, f"Successfully generated a new {len(quiz_data)}-question quiz!")

    except Exception as e:
        logger.error(f"AI quiz generation failed for subject {subject.name} (ID: {subject_id}): {str(e)}")
        messages.error(request, "The AI failed to generate a quiz. Please check your API key or try again.")
    # --- **** END FIX 2 **** ---

    quizzes = Quiz.objects.filter(subject=subject).order_by('-id') # Show newest first
    return render(request, 'planner/quiz.html', {'subject': subject, 'quizzes': quizzes})

# Generate AI Study Plan
def generate_study_plan_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    # Assume exam date is provided or default to 30 days from now
    exam_date_str = request.GET.get('exam_date', (datetime.now().date() + timedelta(days=30)).isoformat())
    exam_date = datetime.fromisoformat(exam_date_str).date()
    start_date = datetime.now().date()
    subjects_data = [{"name": subject.name, "weightage": subject.weightage}]
    
    try:
        plan_data = generate_study_plan(subjects_data, start_date, exam_date)
        for p in plan_data:
            StudyPlan.objects.create(
                subject=subject,
                plan_text=f"{p.get('topics', 'Study')} - {p['hours']} hours"
            )
        messages.success(request, "Successfully generated a new study plan!")
    except Exception as e:
        logger.error(f"AI study plan generation failed for subject {subject.name}: {str(e)}")
        messages.error(request, "The AI failed to generate a study plan. Please try again.")

    studyplans = StudyPlan.objects.filter(subject=subject).order_by('-id')
    return render(request, 'planner/studyplan.html', {
        'subject': subject,
        'studyplans': studyplans,
        'notes': Notes.objects.filter(subject=subject).order_by('-created_at'),
    })

# Download Notes
def download_note(request, note_id):
    note = get_object_or_404(Notes, id=note_id)
    subject_name = note.subject.name.replace(' ', '_').lower()
    filename = f"{subject_name}_notes.txt"
    response = HttpResponse(note.content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response