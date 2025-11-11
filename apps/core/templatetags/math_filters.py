from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide el valor por el argumento"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calcula el porcentaje del valor respecto al total"""
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError):
        return 0

@register.filter
def format_currency(value):
    """Formatea un número como moneda peruana"""
    try:
        return f"S/ {float(value):,.2f}"
    except (ValueError, TypeError):
        return "S/ 0.00"
