from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('subjects/', views.subject_list, name='subjects'),
    path('studyplan/<int:subject_id>/', views.study_plan_list, name='studyplan'),
]
