from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='percentage_of')
def percentage_of(value, total):
    try:
        return round((float(value) / float(total)) * 100, 2)
    except (ValueError, ZeroDivisionError):
        return 0