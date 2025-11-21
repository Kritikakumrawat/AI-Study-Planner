# planner/models.py (Confirmed Ready)

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- 1. SUBJECT MODEL ---

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    syllabus_file = models.FileField(upload_to='syllabus/', blank=True, null=True)
    weightage = models.IntegerField(default=0)

    def __str__(self):
        return self.name

# --- 2. USER PROFILE MODEL ---

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    course_details = models.CharField(max_length=100, blank=True, null=True)
    
    # Field to store the subjects the user has selected (Many-to-Many)
    selected_subjects = models.ManyToManyField(Subject, blank=True) 

    def __str__(self):
        return f"{self.user.username}'s profile"

# --- 3. SIGNAL FOR AUTOMATIC PROFILE CREATION (ROBUST VERSION) ---

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


# --- 4. OTHER STUDY MODELS ---


class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
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
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notes for {self.subject.name}"


class Quiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes')
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1)

    def __str__(self):
        return f"Quiz: {self.question[:50]}..."
    
# --- 5. NEW USER STUDY MATERIAL MODEL ---
class UserStudyMaterial(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    # This field holds the user's specific syllabus copy or notes material
    user_file = models.FileField(upload_to='user_materials/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'subject')

    def __str__(self):
        return f"{self.user.username}'s material for {self.subject.name}"