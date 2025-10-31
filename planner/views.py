from django.shortcuts import render
from .models import Subject, StudyPlan

def home(request):
    return render(request, 'planner/home.html')

def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'planner/subjects.html', {'subjects': subjects})

def study_plan(request, subject_id):
    subject = Subject.objects.get(id=subject_id)
    studyplan = StudyPlan.objects.filter(subject=subject).first()
    return render(request, 'planner/studyplan.html', {'subject': subject, 'studyplan': studyplan})
