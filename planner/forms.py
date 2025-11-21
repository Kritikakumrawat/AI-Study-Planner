from django import forms
# FIX: Import the new model, UserStudyMaterial
from .models import Subject, UserStudyMaterial 

class SubjectSelectionForm(forms.Form):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple, 
        label="Select the subjects you want to learn"
    )

# --- NEW FORM FOR SUBJECT CREATION ---
class SubjectCreateForm(forms.ModelForm):
    class Meta:
        model = Subject
        # Include name and weightage for user input.
        fields = ['name', 'weightage']


# --- NEW FORM FOR USER STUDY MATERIAL UPLOAD ---
class UserStudyMaterialForm(forms.ModelForm):
    """
    Form used by the user to upload their study material (PDF)
    The user and subject fields are set automatically in the view.
    """
    class Meta:
        model = UserStudyMaterial
        # Only expose the file upload field to the user
        fields = ['user_file'] 
        widgets = {
            'user_file': forms.FileInput(attrs={'accept': '.pdf', 'class': 'form-control'}),
        }