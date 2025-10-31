from django.db import models

class Subject(models.Model):
    name = models.CharField(max_length=100)
    syllabus_file = models.FileField(upload_to='syllabus/', blank=True, null=True)
    weightage = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class StudyPlan(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    plan_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Study Plan for {self.subject.name}"


