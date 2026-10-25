# django-nested-modals 0.1 renders forms itself; earlier versions use crispy-forms layout objects
try:
    from django_modals.layout import HTML, StrictButton
except ImportError:
    from crispy_forms.bootstrap import StrictButton
    from crispy_forms.layout import HTML
