# planner/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows accessing a dictionary item by key in Django templates."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None