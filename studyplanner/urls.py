"""
URL configuration for studyplanner project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # NEW: Import settings
from django.conf.urls.static import static # NEW: Import static handler

# Note: Keeping the clean structure, relying on planner.urls for app views.

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This line includes all URLs defined in planner/urls.py
    path('', include('planner.urls')), 
]

# --- REQUIRED FOR SERVING USER UPLOADED FILES (MEDIA) IN DEVELOPMENT ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
# NOTE: The static files (CSS, JS) are handled automatically in development.