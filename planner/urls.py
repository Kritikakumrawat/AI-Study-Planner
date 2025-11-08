from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('subjects/', views.subject_list, name='subjects'),
    path('studyplan/<int:subject_id>/', views.study_plan_list, name='studyplan'),
    path('notes/<int:subject_id>/', views.generate_notes, name='generate_notes'),
    path('quiz/<int:subject_id>/', views.generate_quiz, name='generate_quiz'),
    path('generate_studyplan/<int:subject_id>/', views.generate_study_plan_view, name='generate_study_plan'),
]
