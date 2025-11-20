# planner/templatetags/custom_filters.py

from django import template
from collections import defaultdict 

# --- THIS LINE MUST BE PRESENT AND CORRECT ---
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Retrieves an item from a dictionary using its key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None