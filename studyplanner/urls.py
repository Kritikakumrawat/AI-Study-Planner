# studyplanner/urls.py (Corrected File)

"""
URL configuration for studyplanner project.
... (rest of original comments)
"""
from django.contrib import admin
from django.urls import path, include

# ❌ REMOVE THIS LINE:
# from planner import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ✅ Keep this line - it includes all URLs (including quiz/submit) from planner/urls.py
    path('', include('planner.urls')), 
    
    # ❌ REMOVE THE FOLLOWING LINE:
    # path('quiz/<int:subject_id>/submit/', views.submit_quiz, name='submit_quiz'),
]