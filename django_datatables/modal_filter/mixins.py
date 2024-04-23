import base64
import binascii
import json

from django.urls import reverse
from django_menus.menu import MenuItem
from django_modals.forms import CrispyForm
from django_modals.helper import ajax_modal_replace

from django_datatables.helpers import add_filters
from .modals import DatatableFilterModal


class DatatableFilterField:

    def __init__(self, field_id, field, datatable_field=None, filter_function=None):
        self.field_id = field_id
        self.field = field
        self.datatable_field = datatable_field
        self.filter_function = filter_function

    @staticmethod
    def form_fields(field_list):
        return {f.field_id: f.field for f in field_list}

    def get_filter(self, value, table=None):
        if value is None:
            if self.datatable_field[-4:] == '__in':
                return {self.datatable_field[:-2] + 'isnull': True}
        if self.datatable_field:
            return {self.datatable_field: value}
        elif self.filter_function:
            return self.filter_function(table, self, value)

    @staticmethod
    def get_field(field_list, field_id):
        for f in field_list:
            if f.field_id == field_id:
                return f


class DatatableFilterMixin:

    filter_fields = []
    kwargs: dict

    def filter_menu_items(self):

        buttons = [MenuItem('datatable_filter', 'Filter', font_awesome='fas fa-filter', link_type=MenuItem.AJAX_BUTTON)]
        if 'base64' in self.kwargs:
            buttons.append(MenuItem('clear_filters', 'Clear Filters', font_awesome='fas fa-undo',
                                    css_classes='btn btn-warning', link_type=MenuItem.AJAX_BUTTON))

            # Add buttons showing which filters are being used - needs more work to format correctly and clear filter
            # on pressing button
            # buttons += [MenuItem('clear', f'{k}-{v}', MenuItem.AJAX_BUTTON, css_classes='btn btn-light btn-sm')
            #             for k, v in self.filter_dict.items()]
        return buttons

    def filter_clean(self, form, cleaned_data):
        pass

    def filter_form(self):
        new_form = type('FilterForm', (CrispyForm,), DatatableFilterField.form_fields(self.filter_fields))
        return new_form

    # noinspection PyUnresolvedReferences
    def button_clear_filters(self):
        url_kwargs = self.request.resolver_match.kwargs
        url_kwargs.pop('base64', None)
        return self.command_response('redirect', url=reverse(self.request.resolver_match.url_name, kwargs=url_kwargs))

    # noinspection PyUnresolvedReferences
    def button_datatable_filter(self):
        return self.command_response(ajax_modal_replace(self.request, modal_class=DatatableFilterModal,
                                                        ajax_function='modal_html', form_class=self.filter_form(),
                                                        initial=self.filter_dict))

    def dispatch(self, request, *args, **kwargs):
        # noinspection PyAttributeOutsideInit
        self.filter_dict = self.decode_filter()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, **kwargs):
        if 'modal_id' in request.POST and 'ajax_method' not in request.POST:
            return DatatableFilterModal.as_view()(request, filter_clean=self.filter_clean,
                                                  form_class=self.filter_form(),
                                                  url_name=request.resolver_match.url_name,
                                                  url_kwargs=request.resolver_match.kwargs,
                                                  **kwargs)
        # noinspection PyUnresolvedReferences
        return super().post(request, **kwargs)

    def decode_filter(self):
        if 'base64' in self.kwargs:
            try:
                return json.loads(base64.urlsafe_b64decode(self.kwargs['base64']))
            except binascii.Error:
                raise ValueError('Error')
        return {}

    def add_modal_filter(self, table, max_records=4000, filtered_max_records=20000):
        if table.max_records is None:
            table.max_records = filtered_max_records if self.filter_dict else max_records
        for k, v in self.filter_dict.items():
            table.filter = add_filters(table.filter,
                                       DatatableFilterField.get_field(self.filter_fields, k).get_filter(v, table))
