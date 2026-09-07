from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """Add a CSS class to a bound form field widget."""
    widget = field.field.widget
    attrs = {}
    if hasattr(widget, 'attrs'):
        attrs = dict(widget.attrs)
    attrs['class'] = css_class
    widget.attrs = attrs
    return field