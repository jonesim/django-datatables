from django.forms.fields import CharField

from datatable_examples import models
from datatable_examples.models import Tags
from datatable_examples.views.menu import MainMenu
from django_datatables.datatables import DatatableView
from django_datatables.modal_filter.filter_fields import FilterModelMultipleChoiceField
from django_datatables.modal_filter.mixins import DatatableFilterMixin, DatatableFilterField


class ModalFilterExample(DatatableFilterMixin, MainMenu, DatatableView):
    model = models.Company
    menu_display = 'Modal Filter'

    filter_fields = [
        DatatableFilterField('Company Name',
                             CharField(help_text='Name contains', required=False),
                             datatable_field='name__contains'),
        DatatableFilterField('Tags',
                             FilterModelMultipleChoiceField(queryset=Tags.objects.all()),
                             datatable_field='tags__in')
    ]

    def setup_menu(self):
        self.add_menu('menu', 'buttons').add_items(*self.filter_menu_items())
        super().setup_menu()

    def setup_table(self, table):
        table.add_columns(
            ('id', {'column_defs': {'width': '30px'}}),
            'name',
            'Tags',
            ('dissolved', {'choices': ['yes', 'no']}),
        )
        self.add_modal_filter(table)
