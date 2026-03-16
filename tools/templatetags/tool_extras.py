from django import template

register = template.Library()

@register.filter
def abs_value(value):
    """返回数值的绝对值"""
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return value