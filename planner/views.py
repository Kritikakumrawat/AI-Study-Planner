from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages, auth
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
# --- REQUIRED IMPORTS ---
from .models import UserProfile
from .forms import SubjectSelectionForm, SubjectCreateForm
from .models import Subject, StudyPlan, Notes, Quiz
# ------------------------
from .features.summarizer import summarize_text
from .features.ai_helper import generate_quiz_questions
from .features.study_planner import generate_study_plan
from .features.pdf_reader import extract_text_from_pdf
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)

# Home page
def home(request):
    return render(request, 'planner/home.html')

# List of all subjects (Protected and Filtered for the logged-in user)
@login_required 
def subject_list(request):
    """List subjects selected by the current user."""
    
    if not request.user.is_authenticated:
        return redirect('login') 
        
    try:
        profile = request.user.userprofile
        subjects = profile.selected_subjects.all()
    except Exception as e:
        logger.error(f"Error accessing profile or subjects for user {request.user.username}: {e}")
        messages.error(request, "Error retrieving profile data. Please log in again.")
        # We redirect to 'logout' to clear the corrupted session
        return redirect('logout') 

    return render(request, 'planner/subjects.html', {'subjects': subjects})

# Show study plan and notes for a subject
def study_plan_list(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    studyplans = StudyPlan.objects.filter(subject=subject)
    notes = Notes.objects.filter(subject=subject).order_by('-created_at')
    return render(request, 'planner/studyplan.html', {
        'subject': subject,
        'studyplans': studyplans,
        'notes': notes,
    })

# Display Notes for a subject
def notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    notes = Notes.objects.filter(subject=subject).order_by('-created_at')
    exam = subject.exams.first()  # Assuming one exam per subject
    exam_date = exam.exam_date if exam else None
    return render(request, 'planner/notes.html', {'subject': subject, 'notes': notes, 'exam_date': exam_date})

# Generate AI Notes
def generate_notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    # Check if syllabus file exists
    if not subject.syllabus_file:
        error_message = "No syllabus available for generating notes."
        logger.error(f"No syllabus file for subject {subject.name} (ID: {subject_id})")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})
        else:
            messages.error(request, error_message)
            return redirect('notes', subject_id=subject_id)

    text = ""
    try:
        text = extract_text_from_pdf(subject.syllabus_file.path)
    except Exception as e:
        logger.error(f"Failed to extract text from PDF for subject {subject.name} (ID: {subject_id}): {str(e)}")
        text = ""  # Treat as no text

    if not text:
        text = f"Sample content for {subject.name}. This is placeholder text for AI summarization."

    try:
        generated_text = summarize_text(text)
    except Exception as e:
        error_message = "AI failed to generate notes. Try again."
        logger.error(f"AI summarization failed for subject {subject.name} (ID: {subject_id}): {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})
        else:
            messages.error(request, error_message)
            return redirect('notes', subject_id=subject_id)

    note = Notes.objects.create(subject=subject, content=generated_text, ai_generated=True)

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    else:
        return redirect('notes', subject_id=subject_id)

# Generate Quiz for a subject
def generate_quiz(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    text = ""
    if subject.syllabus_file:
        try:
            text = extract_text_from_pdf(subject.syllabus_file.path)
        except Exception as e:
            logger.error(f"Failed to extract PDF text for quiz (Subject: {subject.id}): {str(e)}")
            text = "" # Fallback to placeholder
            
    if not text:
        text = f"Sample content for {subject.name}. This is placeholder text for quiz generation."

    try:
        quiz_data = generate_quiz_questions(text, num_questions=5)
        
        # Optional: Clear old quizzes before adding new ones
        # Quiz.objects.filter(subject=subject).delete()

        for q in quiz_data:
            Quiz.objects.create(
                subject=subject,
                question=q['question'],
                option_a=q['options'][0] if len(q['options']) > 0 else "",
                option_b=q['options'][1] if len(q['options']) > 1 else "",
                option_c=q['options'][2] if len(q['options']) > 2 else "",
                option_d=q['options'][3] if len(q['options']) > 3 else "",
                correct_answer=q['answer']
            )
        
        messages.success(request, f"Successfully generated a new {len(quiz_data)}-question quiz!")

    except Exception as e:
        logger.error(f"AI quiz generation failed for subject {subject.name} (ID: {subject_id}): {str(e)}")
        messages.error(request, "The AI failed to generate a quiz. Please check your API key or try again.")
        
    quizzes = Quiz.objects.filter(subject=subject).order_by('-id') # Show newest first
    return render(request, 'planner/quiz.html', {'subject': subject, 'quizzes': quizzes})

# Generate AI Study Plan
def generate_study_plan_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    # Assume exam date is provided or default to 30 days from now
    exam_date_str = request.GET.get('exam_date', (datetime.now().date() + timedelta(days=30)).isoformat())
    exam_date = datetime.fromisoformat(exam_date_str).date()
    start_date = datetime.now().date()
    subjects_data = [{"name": subject.name, "weightage": subject.weightage}] 
    
    try:
        plan_data = generate_study_plan(subjects_data, start_date, exam_date)
        for p in plan_data:
            StudyPlan.objects.create(
                subject=subject,
                plan_text=f"{p.get('topics', 'Study')} - {p['hours']} hours"
            )
        messages.success(request, "Successfully generated a new study plan!")
    except Exception as e:
        logger.error(f"AI study plan generation failed for subject {subject.name}: {str(e)}")
        messages.error(request, "The AI failed to generate a study plan. Please try again.")

    studyplans = StudyPlan.objects.filter(subject=subject).order_by('-id')
    return render(request, 'planner/studyplan.html', {
        'subject': subject,
        'studyplans': studyplans,
        'notes': Notes.objects.filter(subject=subject).order_by('-created_at'),
    })

# Download Notes
def download_note(request, note_id):
    note = get_object_or_404(Notes, id=note_id)
    subject_name = note.subject.name.replace(' ', '_').lower()
    filename = f"{subject_name}_notes.txt"
    response = HttpResponse(note.content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# Login view
def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('username')  # This can be username, email, or phone
        password = request.POST.get('password')

        user = None
        # Try to authenticate with username first
        user = authenticate(request, username=identifier, password=password)

        # If not found, try with email
        if user is None:
            try:
                from .models import UserProfile
                profile = UserProfile.objects.get(email=identifier)
                user = authenticate(request, username=profile.user.username, password=password)
            except UserProfile.DoesNotExist:
                pass

        # If not found, try with phone number
        if user is None:
            try:
                from .models import UserProfile
                profile = UserProfile.objects.get(phone_number=identifier)
                user = authenticate(request, username=profile.user.username, password=password)
            except UserProfile.DoesNotExist:
                pass

        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials.')
    return render(request, 'planner/login.html')

# Logout view
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')

# Signup view
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # --- START CORRECTED PROFILE UPDATE LOGIC (Step 16) ---
            # Profile is guaranteed to exist due to the post_save signal. We only update it.
            try:
                profile = user.userprofile
                profile.phone_number = request.POST.get('phone_number')
                profile.email = request.POST.get('email')
                profile.course_details = request.POST.get('course_details')
                profile.save()
            except UserProfile.DoesNotExist:
                # Failsafe: if signal somehow failed (highly unlikely now), create it now
                UserProfile.objects.create(
                    user=user,
                    phone_number=request.POST.get('phone_number'),
                    email=request.POST.get('email'),
                    course_details=request.POST.get('course_details')
                )
            # --- END CORRECTED PROFILE UPDATE LOGIC ---
            
            login(request, user)
            messages.success(request, 'Account created successfully! Now select your subjects.')
            return redirect('select_subjects') # REDIRECTS TO NEW SELECTION VIEW

        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    return render(request, 'planner/signup.html', {'form': form})

# Profile view
@login_required
def profile_view(request):
    return render(request, 'planner/profile.html')

# --- SUBJECT SELECTION VIEW ---

@login_required 
def subject_selection_view(request):
    try:
        profile = request.user.userprofile 
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please log in again.")
        return redirect('logout') # Use the correct URL name 'logout'

    if request.method == 'POST':
        form = SubjectSelectionForm(request.POST)
        if form.is_valid():
            selected_subjects = form.cleaned_data['subjects']
            
            # Update the UserProfile's selected_subjects field
            profile.selected_subjects.set(selected_subjects) 
            
            messages.success(request, "Subjects saved successfully!")
            return redirect('home') 

    else:
        # On GET request, pre-select any subjects already chosen
        initial_data = {'subjects': profile.selected_subjects.all()}
        form = SubjectSelectionForm(initial=initial_data)

    context = {'form': form}
    return render(request, 'planner/subject_selection.html', context)
    
# --- NEW SUBJECT ADDITION VIEW ---

@login_required
def add_subject_view(request):
    """Allows authenticated users to create a new Subject instance."""
    if request.method == 'POST':
        form = SubjectCreateForm(request.POST) # Uses the ModelForm defined in forms.py
        if form.is_valid():
            new_subject = form.save(commit=False)
            new_subject.save() 
            
            # Add the newly created subject to the user's selected subjects immediately
            request.user.userprofile.selected_subjects.add(new_subject)
            
            messages.success(request, f"Subject '{new_subject.name}' added and selected successfully!")
            # Redirect back to the subject list
            return redirect('subjects')
        else:
            messages.error(request, "Failed to add subject. Please check the name.")
    else:
        form = SubjectCreateForm() # Render empty form on GET

    context = {
        'form': form,
        'title': 'Add New Subject'
    }
    
    # NOTE: The frontend team needs to create 'planner/add_subject.html' 
    return render(request, 'planner/add_subject.html', context)