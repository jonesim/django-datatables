import datetime

from django.core.exceptions import ValidationError
from django.forms import CharField, ModelMultipleChoiceField, DateField, MultipleChoiceField, ChoiceField
from django_modals.widgets.jquery_datepicker import DatePicker
from django_modals.widgets.month_picker import MonthPicker
from django_modals.widgets.select2 import Select2Multiple, Select2


class FilterDateField(DateField):

    def prepare_value(self, value):
        if value:
            try:
                date = datetime.datetime.strptime(value, '%Y%m-%d')
                return date.strftime('%d/%m/%Y')
            except ValueError:
                return value

    def __init__(self, **kwargs):
        super().__init__(widget=DatePicker, required=False, **kwargs)


class MonthField(CharField):

    def __init__(self, **kwargs):
        super().__init__(widget=MonthPicker, required=False, **kwargs)

    def prepare_value(self, value):
        if value and type(value) == list:
            try:
                return '{:02d}/{}'.format(value[0], value[1])
            except ValueError:
                return value
        return value

    def clean(self, value):
        if value:
            try:
                date = datetime.datetime.strptime(value, '%m/%Y')
                return [date.month, date.year]
            except ValueError:
                raise ValidationError('Invalid month')


class FilterModelMultipleChoiceField(ModelMultipleChoiceField):

    def __init__(self, **kwargs):
        super().__init__(required=False, widget=Select2Multiple, **kwargs)


class FilterChoiceField(ChoiceField):

    def __init__(self, **kwargs):
        super().__init__(required=False, widget=Select2, **kwargs)


class FilterMultipleChoiceField(MultipleChoiceField):
    def __init__(self, **kwargs):
        super().__init__(required=False, widget=Select2Multiple, **kwargs)
