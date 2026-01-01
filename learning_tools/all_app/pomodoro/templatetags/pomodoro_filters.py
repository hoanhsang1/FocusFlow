from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """Split string by delimiter"""
    return value.split(arg)