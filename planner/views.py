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
from collections import defaultdict # <-- NEW IMPORT for timetable view
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
        # FILTERING: Only show subjects the user has selected
        subjects = profile.selected_subjects.all()
    except Exception as e:
        logger.error(f"Error accessing profile or subjects for user {request.user.username}: {e}")
        messages.error(request, "Error retrieving profile data. Please log in again.")
        return redirect('logout') 

    return render(request, 'planner/subjects.html', {'subjects': subjects})

# --- ADDED TIMETABLE VIEW (Step 24) ---
# planner/views.py (REPLACE timetable_view TEMPORARILY)

# planner/views.py (REPLACE timetable_view)

@login_required
def timetable_view(request):
    """Retrieves all study plans for the current user for display on the timetable page."""
    
    # 1. Filter the study plans by the logged-in user
    # This should now work if your database is finally synchronized
    studyplans = StudyPlan.objects.filter(user=request.user).order_by('created_at')
    
    # 2. Get the user's selected subjects for context/filtering other data
    try:
        profile = request.user.userprofile
        selected_subjects = profile.selected_subjects.all()
    except:
        selected_subjects = Subject.objects.none() # Empty queryset if error

    context = {
        'studyplans': studyplans,
        'selected_subjects': selected_subjects,
        # You may add more data here later (e.g., upcoming exams for the user)
    }
    
    return render(request, 'planner/timetable.html', context)

# Show study plan and notes for a subject
@login_required 
def study_plan_list(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    # FILTERING: Filter by user AND subject
    studyplans = StudyPlan.objects.filter(user=request.user, subject=subject) 
    notes = Notes.objects.filter(user=request.user, subject=subject).order_by('-created_at') 
    return render(request, 'planner/studyplan.html', {
        'subject': subject,
        'studyplans': studyplans,
        'notes': notes,
    })

# Display Notes for a subject
@login_required 
def notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    # FILTERING: Filter by user AND subject
    notes = Notes.objects.filter(user=request.user, subject=subject).order_by('-created_at') 
    
    # NOTE: Exam filtering is complex due to null=True in models.
    exam = subject.exams.filter(user=request.user).first() or subject.exams.first() 
    exam_date = exam.exam_date if exam else None
    
    return render(request, 'planner/notes.html', {'subject': subject, 'notes': notes, 'exam_date': exam_date})

# Generate AI Notes
@login_required 
def generate_notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    # ... (rest of PDF and AI calling logic remains the same) ...
    
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
        text = "" 

    if not text:
        text = f"Sample content for {subject.name}. This is placeholder text for AI summarization."

    try:
        # Use external_summarize for robust AI call
        from .features.ai_helper import external_summarize
        generated_text = external_summarize(text) 
    except Exception as e:
        error_message = "AI failed to generate notes. Try again."
        logger.error(f"AI summarization failed for subject {subject.name} (ID: {subject_id}): {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})
        else:
            messages.error(request, error_message)
            return redirect('notes', subject_id=subject_id)

    # SAVING: Add user=request.user when creating the note
    note = Notes.objects.create(
        user=request.user, 
        subject=subject, 
        content=generated_text, 
        ai_generated=True
    )

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
@login_required 
def generate_quiz(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    text = ""
    if subject.syllabus_file:
        try:
            text = extract_text_from_pdf(subject.syllabus_file.path)
        except Exception as e:
            logger.error(f"Failed to extract PDF text for quiz (Subject: {subject.id}): {str(e)}")
            text = "" 
    
    if not text:
        text = f"Sample content for {subject.name}. This is placeholder text for quiz generation."

    try:
        from .features.ai_helper import generate_quiz_questions
        quiz_data = generate_quiz_questions(text, num_questions=5)
        
        for q in quiz_data:
            # SAVING: Add user=request.user when creating the quiz
            Quiz.objects.create(
                user=request.user, 
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
        messages.error(request, "The AI failed to generate a quiz. Please check your AI service logs.")
        
    # FILTERING: Filter by user AND subject
    quizzes = Quiz.objects.filter(user=request.user, subject=subject).order_by('-id') 
    return render(request, 'planner/quiz.html', {'subject': subject, 'quizzes': quizzes})

# Generate AI Study Plan (Refined to use all user subjects)
@login_required
def generate_study_plan_view(request):
    """Generates an AI study plan based on ALL of the user's selected subjects."""
    
    user = request.user
    
    try:
        profile = user.userprofile
        selected_subjects = profile.selected_subjects.all()
    except UserProfile.DoesNotExist:
        messages.error(request, "Please select your subjects first.")
        return redirect('select_subjects')
    
    if not selected_subjects.exists():
        messages.warning(request, "You need to select subjects before generating a plan.")
        return redirect('select_subjects')

    subjects_data = []
    for subject in selected_subjects:
        subjects_data.append({
            "name": subject.name,
            "weightage": subject.weightage 
        })
        
    exam_date = datetime.now().date() + timedelta(days=30)
    start_date = datetime.now().date()
    
    try:
        from .features.ai_helper import generate_study_plan_ai
        plan_data = generate_study_plan_ai(subjects_data, start_date.isoformat(), exam_date.isoformat())
        
        for p in plan_data:
            subject_name = p.get('subject_name', subjects_data[0]['name'])
            
            try:
                subject_obj = Subject.objects.get(name=subject_name) 
            except Subject.DoesNotExist:
                 logger.warning(f"AI plan generated unknown subject: {subject_name}")
                 continue

            # SAVING: Add user=request.user when creating the plan
            StudyPlan.objects.create(
                user=request.user, 
                subject=subject_obj,
                plan_text=f"Date: {p.get('date', 'N/A')} | Topics: {p.get('topics', 'Study')} - {p.get('hours', 0)} hours"
            )
            
        messages.success(request, "Successfully generated a new study plan!")
        
    except Exception as e:
        logger.error(f"AI study plan generation failed for user {user.username}: {str(e)}")
        messages.error(request, "The AI failed to generate a study plan. Please check your AI service logs.")

    # Redirect to the timetable view to see the result
    return redirect('timetable') 

# Download Notes
@login_required # Added protection
def download_note(request, note_id):
    note = get_object_or_404(Notes, id=note_id)
    # Ensure only the owner can download
    if note.user != request.user:
        messages.error(request, "You do not have permission to download this note.")
        return redirect('notes', subject_id=note.subject.id)
        
    subject_name = note.subject.name.replace(' ', '_').lower()
    filename = f"{subject_name}_notes.txt"
    response = HttpResponse(note.content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# Login view (No changes needed)
def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('username')
        password = request.POST.get('password')

        user = None
        user = authenticate(request, username=identifier, password=password)

        if user is None:
            try:
                profile = UserProfile.objects.get(email=identifier)
                user = authenticate(request, username=profile.user.username, password=password)
            except UserProfile.DoesNotExist:
                pass

        if user is None:
            try:
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

# Logout view (No changes needed)
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')

# Signup view (Corrected in Step 16)
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # --- CORRECTED PROFILE UPDATE LOGIC ---
            try:
                profile = user.userprofile
                profile.phone_number = request.POST.get('phone_number')
                profile.email = request.POST.get('email')
                profile.course_details = request.POST.get('course_details')
                profile.save()
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(
                    user=user,
                    phone_number=request.POST.get('phone_number'),
                    email=request.POST.get('email'),
                    course_details=request.POST.get('course_details')
                )
            
            login(request, user)
            messages.success(request, 'Account created successfully! Now select your subjects.')
            return redirect('select_subjects') 

        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    return render(request, 'planner/signup.html', {'form': form})

# Profile view (No changes needed)
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
        return redirect('logout') 

    if request.method == 'POST':
        form = SubjectSelectionForm(request.POST)
        if form.is_valid():
            selected_subjects = form.cleaned_data['subjects']
            profile.selected_subjects.set(selected_subjects) 
            
            messages.success(request, "Subjects saved successfully!")
            return redirect('home') 

    else:
        initial_data = {'subjects': profile.selected_subjects.all()}
        form = SubjectSelectionForm(initial=initial_data)

    context = {'form': form}
    return render(request, 'planner/subject_selection.html', context)
    
# --- NEW SUBJECT ADDITION VIEW ---
@login_required
def add_subject_view(request):
    """Allows authenticated users to create a new Subject instance."""
    if request.method == 'POST':
        form = SubjectCreateForm(request.POST) 
        if form.is_valid():
            new_subject = form.save(commit=False)
            new_subject.save() 
            
            request.user.userprofile.selected_subjects.add(new_subject)
            
            messages.success(request, f"Subject '{new_subject.name}' added and selected successfully!")
            return redirect('subjects')
        else:
            messages.error(request, "Failed to add subject. Please check the name.")
    else:
        form = SubjectCreateForm() 

    context = {
        'form': form,
        'title': 'Add New Subject'
    }
    return render(request, 'planner/add_subject.html', context)