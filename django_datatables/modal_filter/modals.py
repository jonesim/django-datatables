import datetime

from django.db.models import Model, QuerySet
from django.urls import reverse
from django_modals.helper import base64_json
from django_modals.modals import FormModal


class DatatableFilterModal(FormModal):
    form_class = None
    focus = False
    modal_title = 'Filter'

    def clean(self, form, cleaned_data):
        self.kwargs['filter_clean'](form, cleaned_data)

    @staticmethod
    def convert_field(value):
        if isinstance(value, datetime.date):
            return str(value)
        elif isinstance(value, Model):
            return value.pk
        elif isinstance(value, QuerySet):
            return [o.pk for o in value]
        return value

    def form_valid(self, form):
        query_filter = {k: self.convert_field(v) for k, v in form.cleaned_data.items() if v}
        url_kwargs = self.kwargs['url_kwargs']
        if query_filter:
            url_kwargs['base64'] = base64_json(query_filter)
        else:
            url_kwargs.pop('base64', None)
        return self.command_response('redirect', url=reverse(self.kwargs['url_name'], kwargs=url_kwargs))

    def dispatch(self, request, *args, **kwargs):
        self.form_class = kwargs['form_class']
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return self.kwargs.get('initial')
