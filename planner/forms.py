# planner/forms.py (Add this ModelForm)

from django import forms
from .models import Subject # Make sure Subject is imported

class SubjectSelectionForm(forms.Form):
    # ... (Your existing form remains) ...
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple, 
        label="Select the subjects you want to learn"
    )

# --- NEW FORM FOR SUBJECT CREATION ---
class SubjectCreateForm(forms.ModelForm):
    class Meta:
        model = Subject
        # We only need the user to input the name.
        # syllabus_file and weightage can be added later or default.
        fields = ['name']