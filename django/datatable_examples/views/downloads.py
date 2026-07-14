import csv
import json

from ajax_helpers.mixins import ajax_method
from django.http import HttpResponse
from django_menus.menu import MenuItem

from datatable_examples import models
from datatable_examples.views.base import ManualPage
from django_datatables.columns import SelectColumn
from django_datatables.datatables import DatatableView
from django_datatables.downloads.clipboard import ClipboardCopy
from django_datatables.downloads.excel_download import ExcelDownload
from django_datatables.helpers import send_selected


class RowSelection(ManualPage, DatatableView):
    model = models.Company
    ajax_commands = ['column']
    page_title = 'Row Selection'
    code_examples = ['setup_table', 'selected']

    def setup_menu(self):
        super().setup_menu()
        self.add_menu('page_menu', 'buttons').add_items(
            (send_selected('rowselection', 'selected'), 'Send Selected Ids', MenuItem.JAVASCRIPT),
        )

    @ajax_method
    def selected(self, column_data, table_id):
        selection = json.loads(column_data)
        return self.command_response('message',
                                     text=f'You sent {len(selection)} selected ids from table id {table_id}')

    def setup_table(self, table):
        table.add_columns(
            SelectColumn(hidden=True),
            'id',
            'name',
        )
        table.add_js_filters('selected', 'SelectColumn')

    def add_to_context(self, **kwargs):
        return {'description': (
            '<code>SelectColumn</code> adds a checkbox to every row with select-all / clear header '
            'buttons, and the <b>selected</b> filter block limits the table to ticked rows. The '
            '<code>send_selected</code> helper builds the JavaScript that posts the selected ids to a '
            'view method — tick some rows and press <i>Send Selected Ids</i>.'
        )}


class Downloads(ExcelDownload, ClipboardCopy, ManualPage, DatatableView):
    model = models.Person
    template_name = 'datatable_examples/csv_button_table.html'
    ajax_commands = ['row', 'column']
    page_title = 'Excel, Clipboard & CSV'
    code_examples = ['setup_table', 'column_get_csv']

    def setup_menu(self):
        self.add_menu('menu', 'buttons').add_items(self.download_menu_item(), self.clipboard_menu_item())
        super().setup_menu()

    def column_get_csv(self, **kwargs):
        # Does not filter out hidden columns but can easily be modified
        column_data = json.loads(kwargs['column_data'])
        table = self.tables[kwargs['table_id']]
        self.setup_tables(table_id=table.table_id)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="test.csv"'
        table.filter['id__in'] = column_data
        results = table.get_table_array(self.request, table.get_query())
        writer = csv.writer(response)
        writer.writerow(table.all_titles())
        for r in results:
            writer.writerow(r)
        return response

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'first_name',
            'surname',
            ('company__name', {'title': 'Company Name'}),
        )
        table.add_js_filters('select2', 'company__name')

    def add_to_context(self, **kwargs):
        return {'description': (
            'Three ways to get data out of a table. The <code>ExcelDownload</code> mixin\'s button '
            'exports the current rows to an <code>.xlsx</code> file with openpyxl, and '
            '<code>ClipboardCopy</code> copies them tab-separated for pasting into a spreadsheet — '
            'both respect the active filters. The CSV icon shows a hand-rolled variant: the browser '
            'posts the visible row ids to <code>column_get_csv</code>, which rebuilds the query and '
            'streams a CSV response.'
        )}
