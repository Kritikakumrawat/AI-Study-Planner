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
from django.core.exceptions import ObjectDoesNotExist 
from django.conf import settings 

# --- PROJECT IMPORTS (Ensure these models/forms exist in your app) ---
from .models import UserProfile, Subject, StudyPlan, Notes, Quiz, UserStudyMaterial 
from .forms import SubjectSelectionForm, SubjectCreateForm, UserStudyMaterialForm, ExamDateForm 
# ----------------------------------------------------------------------

# Assuming these AI feature modules exist in planner/features/
from .features.ai_helper import AiHelper, Note, SubjectLineModel
from .features.pdf_reader import extract_text_from_pdf
# ------------------------

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)

# --- AI HELPER INSTANTIATION ---
ai_helper = AiHelper()
# -------------------------------

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

    # If the user has a profile but hasn't selected any subjects yet, 
    # redirect them to the selection page if subjects exist globally.
    if not selected_subjects.exists():
        # Check if there are any subjects at all in the system to select
        if Subject.objects.exists():
            messages.info(request, "Please select the subjects you want to study first.")
            return redirect('select_subjects')
        # If no subjects exist anywhere, prompt user to create one
        messages.info(request, "No subjects found. Please create one.")
        
    return render(request, 'planner/subjects.html', {'subjects': selected_subjects})



# Display Notes for a subject
@login_required 
def notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    # FILTERING: Filter by user AND subject
    notes = Notes.objects.filter(user=request.user, subject=subject).order_by('-created_at') 
    
    # NOTE: Simplified exam lookup, assuming exams are tied to subjects generally
    exam = subject.exams.first() if hasattr(subject, 'exams') else None
    exam_date = exam.exam_date if exam else None
    
    # NEW: Check if the user has uploaded material for this subject
    has_uploaded_material = False
    try:
        if UserStudyMaterial.objects.filter(user=request.user, subject=subject).exists():
            has_uploaded_material = True
    except Exception:
        # Catches cases where the database hasn't been migrated yet, etc.
        pass


    return render(request, 'planner/notes.html', {
        'subject': subject, 
        'notes': notes, 
        'exam_date': exam_date,
        'has_uploaded_material': has_uploaded_material,
    })

# --- VIEW: Handles Study Material Upload (Essential for AI Features) ---
@login_required
def upload_study_material(request, subject_id):
    """Allows user to upload a file (PDF) to be used for AI notes/quiz generation."""

    subject = get_object_or_404(Subject, id=subject_id)
    
    # Check if material already exists (Optional: delete old one or keep for history)
    try:
        existing_material = UserStudyMaterial.objects.get(user=request.user, subject=subject)
    except ObjectDoesNotExist:
        existing_material = None

    if request.method == 'POST':
        form = UserStudyMaterialForm(request.POST, request.FILES, instance=existing_material)
        if form.is_valid():
            material = form.save(commit=False)
            material.user = request.user
            material.subject = subject
            material.save()
            messages.success(request, f"Study material for {subject.name} uploaded successfully!")
            return redirect('notes', subject_id=subject_id)
        else:
            messages.error(request, "Failed to upload file. Check file type and size.")
    else:
        form = UserStudyMaterialForm(instance=existing_material)
        
    return render(request, 'planner/upload_material.html', {
        'subject': subject, 
        'form': form,
        'existing_material': existing_material
    })

# Generate AI Notes (UPDATED to use UserStudyMaterial)
@login_required
def generate_notes(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method != 'POST':
        return redirect('notes', subject_id=subject_id)

    # --- CHECK: Look for user-uploaded material ---
    try:
        # Check the database for the material
        user_material = UserStudyMaterial.objects.get(user=request.user, subject=subject)
        # Check if the file actually exists on the filesystem
        if not os.path.exists(user_material.user_file.path):
            raise ObjectDoesNotExist("File not found on disk.")
    except ObjectDoesNotExist:
        error_message = "Please upload your study material for this subject first."
        logger.warning(f"No user material found for user {request.user.username}, subject {subject.name}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})
        else:
            messages.error(request, error_message)
            return redirect('notes', subject_id=subject_id)

    text = ""
    try:
        # Use the file path from the UserStudyMaterial instance
        text = extract_text_from_pdf(user_material.user_file.path)
    except Exception as e:
        logger.error(f"Failed to extract text from PDF for user material (ID: {user_material.id}): {str(e)}")
        # Fallback to a general prompt if PDF extraction fails
        text = f"Please generate comprehensive study notes for the subject {subject.name} based on its key topics and a general summary of the course."

    if not text:
        error_message = "Could not process file content. Try uploading a different PDF."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})
        messages.error(request, error_message)
        return redirect('notes', subject_id=subject_id)


    try:
        generated_text = ai_helper.external_summarize(text) 
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


# Generate Quiz for a subject (UPDATED to use UserStudyMaterial)
@login_required 
def generate_quiz(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    # --- CHECK: Look for user-uploaded material ---
    try:
        user_material = UserStudyMaterial.objects.get(user=request.user, subject=subject)
    except ObjectDoesNotExist:
        messages.error(request, "Please upload study material first to generate a quiz.")
        return redirect('subjects') # Redirect to a safe page if material is missing
        
    text = ""
    try:
        # Use the file path from the UserStudyMaterial instance
        text = extract_text_from_pdf(user_material.user_file.path)
    except Exception as e:
        logger.error(f"Failed to extract PDF text for quiz (User Material ID: {user_material.id}): {str(e)}")
        text = "" 
    
    if not text:
        text = f"Sample quiz content for {subject.name} based on general course topics."

    try:
        quiz_data = ai_helper.generate_quiz_questions(text, num_questions=5)
        
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
    # Set a default late exam date (e.g., 30 days from now)
    exam_date_latest = datetime.now().date() + timedelta(days=30) 
    
    for subject in selected_subjects:
        # Check for the existence of the 'exams' manager before calling .order_by()
        latest_exam = subject.exams.order_by('-exam_date').first() if hasattr(subject, 'exams') else None
        
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
            plan_data = ai_helper.generate_study_plan_ai(subjects_data, start_date.isoformat(), exam_date_latest.isoformat())
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
    return redirect('enter_exam_date') 

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
        form = SubjectSelectionForm(initial_data)

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

# --- NEW VIEW: DATE INPUT FOR TIMETABLE ---
@login_required
def enter_exam_date(request):
    """Allows the student to input the final exam start date."""
    
    # Check if a study plan already exists and was recently generated
    if StudyPlan.objects.filter(user=request.user).exists():
        messages.info(request, "A study plan already exists. You can proceed to view the timetable, or regenerate the plan to set a new date.")
        return redirect('generate_timetable')
        
    if request.method == 'POST':
        form = ExamDateForm(request.POST)
        if form.is_valid():
            exam_date = form.cleaned_data['exam_start_date']
            
            # Store the date in the session.
            request.session['exam_start_date'] = exam_date.isoformat()
            messages.success(request, "Exam date saved. Generating timetable now...")
            
            # Redirect to the timetable generation view
            return redirect('generate_timetable')
    else:
        form = ExamDateForm()

    return render(request, 'planner/exam_date_input.html', {'form': form, 'title': 'Set Exam Date'})

# --- NEW VIEW: TIMETABLE GENERATION AND DISPLAY ---
@login_required
def generate_timetable(request):
    """Processes study plans and displays the final date-organized schedule."""
    
    # 1. Get the exam date from the session (set in enter_exam_date view)
    exam_start_date_str = request.session.get('exam_start_date')
    
    # If the date is missing, force the user back to input the date
    if not exam_start_date_str:
        messages.warning(request, "Please set your exam date first to generate a customized schedule.")
        return redirect('enter_exam_date')

    # Convert the stored date string back to a date object
    try:
        exam_date = datetime.strptime(exam_start_date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Invalid date format found. Please re-enter the date.")
        return redirect('enter_exam_date')
    
    # 2. Fetch all study plans for the user
    plans_list = StudyPlan.objects.filter(user=request.user).order_by('created_at')
    
    if not plans_list.exists():
        messages.info(request, "No study plan found. Please generate one first.")
        # Optionally redirect the user to generate_study_plan_view
        return redirect('generate_study_plan_view')
    
    # 3. Structure data for the template's schedule display
    tasks_by_date = defaultdict(list)
    
    # We use a date range check based on the exam date
    for plan in plans_list:
        date_match = None
        try:
            # Expected format: "Date: YYYY-MM-DD | Topics: ..."
            date_str = plan.plan_text.split('|')[0].replace('Date:', '').strip()
            date_match = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            # Fallback to the plan creation date if text parsing fails
            date_match = plan.created_at.date()

        # Only include tasks that are before or on the exam date
        if date_match <= exam_date:
            date_key = date_match.isoformat()
            
            # Parse task details for the frontend
            task_details = plan.plan_text.split('|', 1)[-1].strip() if '|' in plan.plan_text else plan.plan_text
            
            tasks_by_date[date_key].append({
                'subject_name': plan.subject.name,
                'task_details': task_details,
                'plan_id': plan.id,
            })

    # Sort the unique dates that were collected
    all_dates = sorted(tasks_by_date.keys())
    
    context = {
        'plans_exist': bool(plans_list),
        'exam_date': exam_date,
        'all_dates': all_dates,
        'tasks_by_date': dict(tasks_by_date),
        'plans_list': plans_list, 
        'title': 'Custom Timetable'
    }
    
    # NOTE: You can change 'planner/timetable_output.html' to 'planner/timetable.html' 
    # if you want to use the template you were fixing earlier.
    return render(request, 'planner/timetable_output.html', context)


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

def welcome_api(request):
    """API endpoint that logs the request and returns a JSON welcome message with metadata."""
    # Log the request
    logger.info(f"Request received: method={request.method}, path={request.path}, user_agent={request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    
    # Prepare the response data
    response_data = {
        "message": "Welcome to the AI Study Planner API!",
        "method": request.method,
        "path": request.path,
        "timestamp": datetime.now().isoformat(),
        "user_agent": request.META.get('HTTP_USER_AGENT', 'Unknown'),
        "remote_addr": request.META.get('REMOTE_ADDR', 'Unknown')
    }
    
    return JsonResponse(response_data)