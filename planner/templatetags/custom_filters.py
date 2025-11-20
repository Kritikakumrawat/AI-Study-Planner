# planner/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows accessing a dictionary item by key in Django templates."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def get_option(quiz, answer_key):
    """Returns the option text for a given answer key (A, B, C, D)."""
    options = {
        'A': quiz.option_a,
        'B': quiz.option_b,
        'C': quiz.option_c,
        'D': quiz.option_d,
    }
    return options.get(answer_key.upper(), 'N/A')
