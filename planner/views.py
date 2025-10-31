from django.shortcuts import render, get_object_or_404
from .models import Subject, StudyPlan, Notes

def home(request):
    return render(request, 'planner/home.html')

def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'planner/subjects.html', {'subjects': subjects})

def study_plan_list(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    studyplans = StudyPlan.objects.filter(subject=subject)
    notes = Notes.objects.filter(subject=subject).order_by('-created_at')
    return render(request, 'planner/studyplan.html', {
        'subject': subject,
        'studyplans': studyplans,
        'notes': notes,
    })
