from django import template
from bufe.utils import is_bufeadmin

register = template.Library()


@register.filter(name='is_bufeadmin')
def is_bufeadmin_filter(user):
    """
    Template filter to check if user is a bufeadmin.
    Usage: {% if user|is_bufeadmin %}
    """
    return is_bufeadmin(user)
