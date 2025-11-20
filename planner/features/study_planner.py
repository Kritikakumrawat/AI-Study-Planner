# planner/features/study_planner.py (Complete Corrected File)

from datetime import datetime, timedelta
from typing import List, Dict
import random

def generate_study_plan(subjects: List[Dict], start_date: datetime, exam_date: datetime) -> List[Dict]:
    """
    Generates a simple study plan based on subject weightage, ensuring the output
    structure matches the expected keys in views.py.
    
    subjects: list of dict { "name": str, "weightage": int }
    start_date, exam_date: datetime objects
    Returns list of dicts: {subject_name, date, hours, topics}
    """
    
    if not subjects or exam_date <= start_date:
        return []

    days = (exam_date - start_date).days
    total_weight = sum(s.get("weightage", 0) for s in subjects) or 1
    hours_per_day = 3  # Standard total study hours per day
    plan = []
    
    # Create a list of subjects weighted by their relative importance
    weighted_subjects = []
    for s in subjects:
        # Calculate proportion and base hours for this subject
        proportion = s.get("weightage", 1) / total_weight
        base_hours = round(hours_per_day * proportion, 1)
        
        # Ensure minimum study hours if subject is selected
        if base_hours < 0.5:
            base_hours = 0.5
            
        # Add a task for this subject for every day, weighted by its calculated hours
        for _ in range(int(round(base_hours * 2))): # Multiply by 2 to increase frequency
             weighted_subjects.append(s['name'])

    
    # Generate daily plan by picking tasks from the weighted list
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # Select a subject for focused study for that day
        if weighted_subjects:
            focused_subject_name = random.choice(weighted_subjects)
            
            # Find the subject object to get its weightage again
            subject_data = next((s for s in subjects if s['name'] == focused_subject_name), None)
            
            if subject_data:
                # Use a standard chunk of time for simplicity in the simulation
                study_hours = random.choice([2.0, 2.5, 3.0]) 

                plan.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "subject_name": focused_subject_name, # <-- CORRECTED KEY
                    "hours": study_hours,
                    "topics": f"High Priority Review: Topics based on weightage {subject_data.get('weightage', 1)}%" # <-- ADDED KEY
                })
                
    return plan