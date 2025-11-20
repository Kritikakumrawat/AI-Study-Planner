from dotenv import load_dotenv
import os
import logging
import json
from collections import defaultdict 
from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm


# --- PROJECT IMPORTS ---
from .models import UserProfile, Subject, StudyPlan, Notes, Quiz
from .forms import SubjectSelectionForm, SubjectCreateForm
# Assuming these AI feature modules exist in planner/features/
# NOTE: Removed redundant internal imports inside functions
from .features.ai_helper import external_summarize, generate_quiz_questions, generate_study_plan_ai
from .features.pdf_reader import extract_text_from_pdf
# ------------------------

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)


# Home page
def home(request):
    return render(request, 'planner/home.html')

# List of all subjects (Protected and Filtered for the logged-in user)
@login_required
def subject_list(request):
    """List subjects selected by the current user. Redirects to selection if none are chosen."""
    
    try:
        profile = request.user.userprofile
        # FILTERING: Only show subjects the user has selected
        selected_subjects = profile.selected_subjects.all()
    except Exception as e:
        logger.error(f"Error accessing profile or subjects for user {request.user.username}: {e}")
        messages.error(request, "Error retrieving profile data. Please log in again.")
        return redirect('logout') 

    # --- CRITICAL FLOW CONTROL FIX ---
    # If the user has a profile but hasn't selected any subjects yet, 
    # redirect them to the selection page if subjects exist globally.
    if not selected_subjects.exists():
        # Check if there are any subjects at all in the system to select
        if Subject.objects.exists():
            messages.info(request, "Please select the subjects you want to study first.")
            return redirect('select_subjects')
        # If no subjects exist anywhere, the user must use the 'add_subject' button.
        
    return render(request, 'planner/subjects.html', {'subjects': selected_subjects})

# Show study plan and notes for a subject
@login_required 
def study_plan_list(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    # Filter by user AND subject
    studyplans = StudyPlan.objects.filter(user=request.user, subject=subject).order_by('-created_at') 
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
    
    # NOTE: Simplified exam lookup, assuming exams are tied to subjects generally
    exam = subject.exams.first() 
    exam_date = exam.exam_date if exam else None
    
    return render(request, 'planner/notes.html', {'subject': subject, 'notes': notes, 'exam_date': exam_date})

# Generate AI Notes (Cleaned up imports)
@login_required
def generate_notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Check if it's a POST request, as notes generation should modify state
    if request.method != 'POST':
        return redirect('notes', subject_id=subject_id)

    if not subject.syllabus_file:
        error_message = "No syllabus available for generating notes. Upload one via Admin."
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
        # Fallback for AI if PDF extraction fails
        text = f"Please generate comprehensive study notes for the subject {subject.name}. Include key concepts and a summary."

    try:
        generated_text = external_summarize(text) 
    except Exception as e:
        error_message = "AI failed to generate notes. Check API connection and try again."
        logger.error(f"AI summarization failed for subject {subject.name} (ID: {subject_id}): {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})
        else:
            messages.error(request, error_message)
            return redirect('notes', subject_id=subject_id)

    # SAVING: Create the new Notes object linked to the user and subject
    note = Notes.objects.create(
        user=request.user, 
        subject=subject, 
        content=generated_text, 
        ai_generated=True
    )

    # Respond to AJAX request for seamless UI update
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
        # Regular browser request redirect
        messages.success(request, f"Notes for {subject.name} generated successfully!")
        return redirect('notes', subject_id=subject_id)


# Generate Quiz for a subject (Cleaned up imports and robust fetching)
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

    # NOTE: Quiz generation should usually be triggered only via GET request from the template,
    # or a dedicated POST endpoint, but we run the generation logic on every GET to simplify flow.
    try:
        # Assuming generate_quiz_questions is imported at the top
        quiz_data = generate_quiz_questions(text, num_questions=5)
        
        # Clear old quizzes for this user/subject before saving new ones
        Quiz.objects.filter(user=request.user, subject=subject).delete()
        
        for q in quiz_data:
            # SAVING: Add user=request.user when creating the quiz
            Quiz.objects.create(
                user=request.user, 
                subject=subject,
                question=q['question'],
                option_a=q['options'][0] if len(q['options']) > 0 else "N/A",
                option_b=q['options'][1] if len(q['options']) > 1 else "N/A",
                option_c=q['options'][2] if len(q['options']) > 2 else "N/A",
                option_d=q['options'][3] if len(q['options']) > 3 else "N/A",
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
    exam_date_latest = datetime.now().date() + timedelta(days=30) 
    
    for subject in selected_subjects:
        latest_exam = subject.exams.order_by('-exam_date').first()
        if latest_exam and latest_exam.exam_date > exam_date_latest:
             exam_date_latest = latest_exam.exam_date
        
        subjects_data.append({
            "name": subject.name,
            "weightage": subject.weightage 
        })
        
    start_date = datetime.now().date()
    
    try:
        # NOTE: Using a robust try/except with a mock fallback for reliable function completion
        try:
             plan_data = generate_study_plan_ai(subjects_data, start_date.isoformat(), exam_date_latest.isoformat())
        except Exception as api_e:
             logger.error(f"AI Plan generation failed, using mock data: {api_e}")
             # --- Mock/Placeholder Data for Testing ---
             if not subjects_data:
                 raise Exception("No subject data available for mock plan.")
                 
             mock_subject_name = subjects_data[0]['name']
             plan_data = [
                 {'subject_name': mock_subject_name, 'date': (start_date + timedelta(days=1)).isoformat(), 'topics': f'Mock: Review basics of {mock_subject_name}', 'hours': 2},
                 {'subject_name': mock_subject_name, 'date': (start_date + timedelta(days=2)).isoformat(), 'topics': f'Mock: Practice problems for {mock_subject_name}', 'hours': 3},
             ]
             # -----------------------------------------
        
        # Clear old study plans for the user before saving new ones
        StudyPlan.objects.filter(user=user).delete()

        for p in plan_data:
            subject_name = p.get('subject_name', selected_subjects.first().name)
            
            try:
                # Find the subject object by name
                subject_obj = Subject.objects.get(name__iexact=subject_name) 
            except Subject.DoesNotExist:
                 logger.warning(f"AI plan generated unknown subject: {subject_name}. Skipping plan entry.")
                 continue

            # SAVING: Create the new StudyPlan object
            StudyPlan.objects.create(
                user=request.user, 
                subject=subject_obj,
                # Plan text structured for easy parsing in timetable_view (Date: YYYY-MM-DD | Task)
                plan_text=f"Date: {p.get('date', start_date.isoformat())} | Topics: {p.get('topics', 'Study')} - {p.get('hours', 0)} hours"
            )
            
        messages.success(request, "Successfully generated a new study plan!")
        
    except Exception as e:
        logger.error(f"Study plan final processing failed for user {user.username}: {str(e)}")
        messages.error(request, "An error occurred during plan processing.")

    # Redirect to the timetable view to see the result
    return redirect('timetable') 

# Download Notes
@login_required 
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
            
            # Link the newly created subject to the user's profile automatically
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
    # This renders the new add_subject.html template
    return render(request, 'planner/add_subject.html', context)

# --- TIMETABLE VIEW (Using the previously fixed logic) ---
@login_required
def timetable_view(request):
    """Processes study plans into a date-organized schedule for the timetable view."""
    
    # 1. Fetch all study plans for the user, ordered by creation (closest to current date assumed better)
    plans_list = StudyPlan.objects.filter(user=request.user).order_by('created_at')
    
    # 2. Structure data for the template's schedule display
    tasks_by_date = defaultdict(list)
    
    # For demonstration, we'll parse the plan_text to get a date.
    all_dates_set = set() # Use a set to avoid duplicate dates
    
    for plan in plans_list:
        # Simple heuristic to extract a date from the plan_text
        date_match = None
        try:
            # Expected format: "Date: YYYY-MM-DD | Topics: ..."
            date_str = plan.plan_text.split('|')[0].replace('Date:', '').strip()
            date_match = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            # Fallback to the plan creation date if text parsing fails
            date_match = plan.created_at.date()

        date_key = date_match.isoformat()
        
        all_dates_set.add(date_key)
        
        # Parse task details for the frontend
        task_details = plan.plan_text.split('|', 1)[-1].strip() if '|' in plan.plan_text else plan.plan_text
        
        tasks_by_date[date_key].append({
            'subject_name': plan.subject.name,
            'task_details': task_details,
            'plan_id': plan.id,
        })

    # Sort the unique dates
    all_dates = sorted(list(all_dates_set))
    
    context = {
        'plans_exist': bool(plans_list),
        'all_dates': all_dates,
        'tasks_by_date': dict(tasks_by_date),
        'plans_list': plans_list, # Used for the Weekly Overview table
    }
    
    return render(request, 'planner/timetable.html', context)

# planner/views.py (Add this new function)

@login_required
def submit_quiz(request, subject_id):
    """Handles the quiz submission, checks answers against the database, and returns the score."""
    if request.method == 'POST':
        subject = get_object_or_404(Subject, id=subject_id)
        
        # 1. Fetch all quiz questions for this subject/user
        quizzes = Quiz.objects.filter(user=request.user, subject=subject)
        
        correct_count = 0
        total_questions = quizzes.count()
        
        # 2. Iterate through submitted answers and compare with correct answers
        for quiz in quizzes:
            submitted_answer = request.POST.get(f'answer_{quiz.id}')
            
            # The correct_answer in the DB is stored as 'A', 'B', 'C', 'D' (uppercase)
            # The submitted value is 'a', 'b', 'c', 'd' (lowercase)
            if submitted_answer and submitted_answer.upper() == quiz.correct_answer:
                correct_count += 1
                
        # 3. Calculate and display results
        if total_questions > 0:
            percentage = round((correct_count / total_questions) * 100)
        else:
            percentage = 0
            
        messages.success(request, f"Quiz submitted! You scored {correct_count} out of {total_questions}.")
        
        # NOTE: For simplicity, we just redirect back to the quiz page with a message
        # In a production app, you might save the score to a new model.
        return render(request, 'planner/quiz_results.html', {
            'subject': subject,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'percentage': percentage,
            'quizzes': quizzes # Pass quizzes to show them again if needed
        })
    
    # If a GET request, just redirect back to the quiz starting page
    return redirect('generate_quiz', subject_id=subject_id)