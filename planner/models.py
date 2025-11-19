# planner/models.py (Complete, Corrected File)

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- 1. SUBJECT MODEL ---

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True) # Added unique=True for clean data
    syllabus_file = models.FileField(upload_to='syllabus/', blank=True, null=True)
    weightage = models.IntegerField(default=0)

    def __str__(self):
        return self.name

# --- 2. USER PROFILE MODEL (CORRECTED) ---

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    course_details = models.CharField(max_length=100, blank=True, null=True)
    
    # ADDED: Field to store the subjects the user has selected (Many-to-Many)
    selected_subjects = models.ManyToManyField(Subject, blank=True) 

    def __str__(self):
        return f"{self.user.username}'s profile"

# --- 3. SIGNAL FOR AUTOMATIC PROFILE CREATION (ROBUST VERSION) ---

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # This logic runs whenever a User object is saved (signup or login)
    
    if created:
        # If the User was just created (signup), create the linked UserProfile immediately
        UserProfile.objects.create(user=instance)
    
    # Ensure the profile is saved/updated when the User is saved (login/update)
    # The try/except handles transient errors during initial creation or access
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        # If it truly doesn't exist but the user exists, create it
        UserProfile.objects.create(user=instance)


# --- 4. OTHER STUDY MODELS (REMAINING AS IS) ---

class StudyPlan(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    plan_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Study Plan for {self.subject.name}"

class Exam(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    exam_date = models.DateField()
    total_marks = models.IntegerField(default=100)
    marks_obtained = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.subject.name} - {self.exam_date}"


class Notes(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notes for {self.subject.name}"


class Quiz(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes')
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1)

    def __str__(self):
        return f"Quiz: {self.question[:50]}..."