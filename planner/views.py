from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Subject, StudyPlan, Notes, Quiz
from .features.summarizer import summarize_text
from .features.ai_helper import generate_quiz_questions
from .features.study_planner import generate_study_plan
from .features.pdf_reader import extract_text_from_pdf
from datetime import datetime

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

# Generate AI Notes
def generate_notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    text = ""
    if subject.syllabus_file:
        text = extract_text_from_pdf(subject.syllabus_file.path)
    if not text:
        text = f"Sample content for {subject.name}. This is placeholder text for AI summarization."
    generated_text = summarize_text(text)
    Notes.objects.create(subject=subject, content=generated_text, ai_generated=True)
    notes = Notes.objects.filter(subject=subject)
    return render(request, 'planner/notes.html', {'subject': subject, 'notes': notes})

# Generate Quiz for a subject
def generate_quiz(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    text = ""
    if subject.syllabus_file:
        text = extract_text_from_pdf(subject.syllabus_file.path)
    if not text:
        text = f"Sample content for {subject.name}. This is placeholder text for quiz generation."
    quiz_data = generate_quiz_questions(text, num_questions=5)
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
    quizzes = Quiz.objects.filter(subject=subject)
    return render(request, 'planner/quiz.html', {'subject': subject, 'quizzes': quizzes})

# Generate AI Study Plan
def generate_study_plan_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    # Assume exam date is provided or default to 30 days from now
    exam_date_str = request.GET.get('exam_date', (datetime.now().date() + datetime.timedelta(days=30)).isoformat())
    exam_date = datetime.fromisoformat(exam_date_str).date()
    start_date = datetime.now().date()
    subjects_data = [{"name": subject.name, "weightage": subject.weightage}]
    plan_data = generate_study_plan(subjects_data, start_date, exam_date)
    for p in plan_data:
        StudyPlan.objects.create(
            subject=subject,
            plan_text=f"{p.get('topics', 'Study')} - {p['hours']} hours"
        )
    studyplans = StudyPlan.objects.filter(subject=subject)
    return render(request, 'planner/studyplan.html', {
        'subject': subject,
        'studyplans': studyplans,
        'notes': Notes.objects.filter(subject=subject).order_by('-created_at'),
    })
