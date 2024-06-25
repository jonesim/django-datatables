import json
from types import MethodType

from ajax_helpers.utils import ajax_command
from crispy_forms.bootstrap import StrictButton
from crispy_forms.layout import HTML
from django.utils.safestring import mark_safe
from django_menus.menu import MenuItem
from django_modals.forms import CrispyForm
from django_modals.modals import FormModal

from datatable_examples import models
from datatable_examples.views.menu import MainMenu
from django_datatables.columns import DatatableColumn

from django_datatables.datatables import DatatableView, DatatableTable


class TestColumn(DatatableColumn):

    def row_result(self, data_dict, page_results):
        result = MethodType(self._ColumnBase__row_result, self)(data_dict, page_results)
        return json.dumps({'data': result, 'class': self.cell_options['class']})

    def col_setup(self):
        self.field = 'name'
        self.column_defs['width'] = 400
        self.spreadsheet = {'editor': 'spreadsheets.custom_column', 'stripHTML': False}
        self.cell_options = {'class': 'text-secondary table-primary '}

class SpreadsheetExample(MainMenu, DatatableView):
    template_name = 'datatable_examples/spreadsheet.html'
    model = models.Company

    def setup_menu(self):
        super().setup_menu()
        self.add_menu('top_menu', 'buttons').add_items(
            MenuItem(ajax_command('send_spreadsheet', table_id='spreadsheetexample'),
                     'SEND DATA', MenuItem.AJAX_COMMAND),
            MenuItem(ajax_command('set_cell', table_id='spreadsheetexample', cell='C2',
                                  value={'data': '4', 'class': 'table-danger'}),
                     'SET CELL', MenuItem.AJAX_COMMAND),
            'spreadsheet_modal')

    def row_changed(self, data, row_no, column, **_kwargs):
        return self.command_response('message', text=f'Data {row_no}:{column} changed {data}')

    def setup_table(self, table):
        table.add_columns(
            '.id', ('name' , {'width': 400}), TestColumn(),
        )
        table.ajax_data = False
        table.max_records = 4
        table.table_options['hide_index'] = False
        table.table_options['on_change'] = 'row' # could be whole
        table.spreadsheet_config = {
            # 'allowInsertRow': False,
            'minSpareRows': 3,
            'nestedHeaders': [[{'title': 'Grouped Header', 'colspan': '3'}]]
        }
        table.datatable_template = 'datatables/spreadsheet.html'

    def button_spreadsheet(self, **kwargs):
        return self.command_response('message', text=kwargs['data'])


class SpreadsheetModal(FormModal):

    form_class = CrispyForm
    modal_title = 'Spreadsheet'
    menu_display = 'Modal'

    @staticmethod
    def submit():
        return StrictButton('Submit',
                            onclick=mark_safe("django_modal.process_commands_lock("
                                              "[{'function': 'post_modal', 'button': spreadsheets.get_sheet_data()}])"),
                            css_class='btn-success modal-submit')

    def form_setup(self, form, **_kwargs):
        table = DatatableTable(table_id='modal-sheet', model=models.Company)
        table.add_columns('id', ('name' , {'width': 400}))
        table.datatable_template = 'datatables/spreadsheet.html'
        table.max_records = 10
        form.buttons = [self.submit(), form.cancel_button()]
        return [HTML(table.render())]

    def form_valid(self, form):
        self.add_command('close')
        return self.command_response('message', text=form.data['modal-sheet'])
