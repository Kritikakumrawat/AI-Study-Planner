from django.contrib import admin
from .models import Subject, StudyPlan, Exam, Notes, Quiz

admin.site.register(Subject)
admin.site.register(StudyPlan)
admin.site.register(Exam)
admin.site.register(Notes)
admin.site.register(Quiz)
