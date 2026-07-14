import csv
import json

from django.http import HttpResponse

from django_datatables.columns import SelectColumn
from django_datatables.constants import HIDE_VISIBILTY, HIDE_OPTIONAL, HIDE_OMIT
from datatable_examples import models
from datatable_examples.views.menu import MainMenu
from django_datatables.column_visibility.mixins import ColumnVisibilityMixin
from django_datatables.datatables import DatatableView
from django_datatables.downloads.clipboard import ClipboardCopy
from django_datatables.downloads.excel_download import ExcelDownload


class HideColumns(ColumnVisibilityMixin, MainMenu, ExcelDownload, ClipboardCopy, DatatableView):
    model = models.Person
    template_name = 'datatable_examples/csv_button_table.html'
    ajax_commands = ['row', 'column']
    menu_display = 'Hide Columns'

    def setup_menu(self):
        self.add_menu('menu', 'buttons').add_items(self.download_menu_item(), self.clipboard_menu_item())
        super().setup_menu()


    def setup_table(self, table):
        table.edit_fields = ['company__name']
        table.edit_options = {'company__name': {'select2': True}}

        table.add_columns(
            SelectColumn(hidden=True),
            ('.id',{'options': {'initial_filter': {'1':  False, '102': False}}} ),
            ('first_name', {'hide_options': HIDE_OPTIONAL}),
            ('company__name', {'title': 'Company Name'}),
            ('company__collink_1', {'hide_options': HIDE_OMIT}),
        )
        if 'pk' in self.kwargs:
            table.filter = {'company__id': self.kwargs['pk']}
        table.add_js_filters('select2', 'company__name')
        table.add_js_filters('pivot', 'id')
        table.add_js_filters('selected', 'SelectColumn')  # can take menu=
        #table.add_js_filters('totals', 'id')
        # self.add_options({
        #     'rowGroup': {'dataSrc': 'company__name',
        #                  }
        #  })
        table.hidden_side_bar = True
        table.table_options['ajax_url'] = self.request.path
        table.show_column_modal = True

    def add_to_context(self, **kwargs):
        context = {'description': '''
        Remove one column in mobile mode.<br>
        Filter on pk if supplied in url.
        '''}

        if 'pk' in self.kwargs:
            context['title'] = type(self).__name__ + ' ' + ' pk:' + str(self.kwargs['pk'])
        else:
            context['title'] = type(self).__name__
        return context
