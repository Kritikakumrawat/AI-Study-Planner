from django import template

# The 'register' variable is mandatory for defining tags and filters
register = template.Library()

# Define the 'get_item' filter used in your template
# This allows you to look up an item in a dictionary (like tasks_by_date)
# using a variable (like date_str) in the template: tasks_by_date|get_item:date_str
@register.filter
def get_item(dictionary, key):
    """
    Returns the value for a given key from a dictionary.
    Safe access filter for Python dictionaries in templates.
    """
    return dictionary.get(key)