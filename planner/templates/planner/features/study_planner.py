# planner/features/study_planner.py
from datetime import datetime, timedelta
from typing import List, Dict

def generate_study_plan(subjects: List[Dict], start_date: datetime, exam_date: datetime) -> List[Dict]:
    """
    subjects: list of dict { "name": str, "weightage": int } weightage optional (defaults to 1)
    start_date, exam_date: datetime objects
    Returns list of dicts: {subject, date (YYYY-MM-DD), hours}
    This is a simple weighted-distribution planner.
    """
    if exam_date <= start_date:
        return []

    days = (exam_date - start_date).days
    # compute weights
    total_weight = sum(s.get("weightage", 1) for s in subjects) or 1
    plan = []
    # distribute hours per day (you can later change per-user avail hours)
    hours_per_day = 3  # default study hours per day; backend can override
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        # choose subject for that day by weighted rotation
        # simple approach: pick subject index based on day mod len(subjects)
        # but allocate hours proportional to weight
        for s in subjects:
            proportion = s.get("weightage", 1) / total_weight
            hours = round(hours_per_day * proportion, 1)
            plan.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "subject": s["name"],
                "hours": hours
            })
    return plan
