from django.shortcuts import render, get_object_or_404
from .models import Subject, StudyPlan, Notes

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

# Placeholder AI Notes (for now, just static)
def generate_notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    generated_text = f"AI-generated notes for {subject.name} will be added here soon!"
    Notes.objects.create(subject=subject, content=generated_text, ai_generated=True)
    notes = Notes.objects.filter(subject=subject)
    return render(request, 'planner/notes.html', {'subject': subject, 'notes': notes})
