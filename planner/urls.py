# planner/urls.py (Complete File)

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('subjects/', views.subject_list, name='subjects'),
    
    # --- ADDED TIMETABLE URL (Step 24) ---
    path('timetable/', views.timetable_view, name='timetable'), 
    
    path('studyplan/<int:subject_id>/', views.study_plan_list, name='studyplan'),
    path('notes/<int:subject_id>/', views.notes, name='notes'),
    path('generate_notes/<int:subject_id>/', views.generate_notes, name='generate_notes'),
    path('quiz/<int:subject_id>/', views.generate_quiz, name='generate_quiz'),
    
    # NOTE: generate_study_plan_view handles ALL subjects now, so the URL should be changed to remove <int:subject_id>
    path('generate_studyplan/', views.generate_study_plan_view, name='generate_study_plan'), # <-- CORRECTED URL
    
    path('download_note/<int:note_id>/', views.download_note, name='download_note'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
    
    # --- USER FLOWS ---
    path('select-subjects/', views.subject_selection_view, name='select_subjects'), 
    path('add-subject/', views.add_subject_view, name='add_subject'),
    # planner/urls.py (Add this line)

    path('quiz/<int:subject_id>/submit/', views.submit_quiz, name='submit_quiz'),
]