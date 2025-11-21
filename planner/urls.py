from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
    path('subjects/', views.subject_list, name='subjects'),
    path('select_subjects/', views.subject_selection_view, name='select_subjects'),
    path('add_subject/', views.add_subject_view, name='add_subject'),
    path('subjects/<int:subject_id>/', views.study_plan_list, name='study_plan_list'),
    path('subjects/<int:subject_id>/notes/', views.notes, name='notes'),
    
    # --- NEW PATH ADDED: This is where users upload their files ---
    path('subjects/<int:subject_id>/upload_material/', views.upload_study_material, name='upload_material'),
    
    path('subjects/<int:subject_id>/generate_notes/', views.generate_notes, name='generate_notes'),
    path('subjects/<int:subject_id>/download_note/<int:note_id>/', views.download_note, name='download_note'),
    path('subjects/<int:subject_id>/quiz/', views.generate_quiz, name='generate_quiz'),
    path('subjects/<int:subject_id>/quiz/submit/', views.submit_quiz, name='submit_quiz'),
    path('generate_study_plan/', views.generate_study_plan_view, name='generate_study_plan'),
    path('timetable/', views.timetable_view, name='timetable'),
    path('api/welcome/', views.welcome_api, name='welcome_api'),
]