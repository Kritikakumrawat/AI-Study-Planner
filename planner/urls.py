from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('subjects/', views.subject_list, name='subjects'),
    path('studyplan/<int:subject_id>/', views.study_plan_list, name='studyplan'),
    path('notes/<int:subject_id>/', views.notes, name='notes'),
    path('generate_notes/<int:subject_id>/', views.generate_notes, name='generate_notes'),
    path('quiz/<int:subject_id>/', views.generate_quiz, name='generate_quiz'),
    path('generate_studyplan/<int:subject_id>/', views.generate_study_plan_view, name='generate_study_plan'),
    path('download_note/<int:note_id>/', views.download_note, name='download_note'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
]
