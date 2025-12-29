from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Permet d'accéder à un dict avec une clé variable dans les templates"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, key)
    return key
