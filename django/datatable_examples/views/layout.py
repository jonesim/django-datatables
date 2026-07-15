import json

from ajax_helpers.utils import ajax_command
from crispy_forms.bootstrap import StrictButton
from crispy_forms.layout import HTML
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.views.generic import FormView, TemplateView
from django_menus.menu import MenuItem
from django_modals.forms import CrispyForm
from django_modals.modals import FormModal

from datatable_examples import models
from datatable_examples.views.base import ManualPage
from django_datatables.columns import ColumnBase, DatatableColumn
from django_datatables.datatables import DatatableTable, DatatableView, HorizontalTable
from django_datatables.plugins.column_totals import ColumnTotals
from django_datatables.reorder_datatable import reorder
from django_datatables.widgets import DataTableReorderWidget, DataTableWidget


class MultipleTables(ManualPage, DatatableView):
    model = models.Company
    template_name = 'datatable_examples/two_tables.html'
    page_title = 'Multiple Tables'
    code_examples = ['add_tables', 'setup_t1', 'setup_t2']

    def add_tables(self):
        self.add_table('t1', model=models.Company)
        self.add_table('t2', model=models.Person)

    @staticmethod
    def setup_t1(table):
        table.add_columns(
            'id',
            'name',
        )
        table.table_options['no_col_search'] = True

    @staticmethod
    def setup_t2(table):
        table.add_columns(
            'id',
            'first_name',
        )

    def add_to_context(self, **kwargs):
        return {'description': (
            'A view can hold any number of tables. Override <code>add_tables</code> to register each '
            'with an id and model, then configure each in its own <code>setup_&lt;table_id&gt;</code> '
            'method. The template receives them as <code>datatables.t1</code>, '
            '<code>datatables.t2</code>, … instead of the single <code>datatable</code>.'
        )}


class HorizontalTablePage(ManualPage, TemplateView):
    template_name = 'datatable_examples/horizontal.html'
    page_title = 'Horizontal Table'
    code_examples = ['get_context_data']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = models.Person.objects.first()
        if person:  # nothing to show until the demo data is imported
            context['datatable'] = HorizontalTable(model=models.Person, pk=person.id).add_columns(
                'id',
                'first_name',
                'company_id',
                'company__company_link'
            )
        return context

    def add_to_context(self, **kwargs):
        return {'description': (
            '<code>HorizontalTable</code> displays a single record with the column titles down the '
            'left — a detail view built from the same column definitions as a normal table. It '
            'renders standalone from any view: give it a model and a <code>pk</code> and drop '
            '<code>datatable</code> into the context.'
        )}


class NoModelData(ManualPage, DatatableView):
    template_name = 'datatable_examples/no_model.html'
    page_title = 'Table Without a Model'
    code_examples = ['add_tables', '_add_columns', 'get_table_query', 'setup_static_version']

    def add_tables(self):
        self.add_table('ajax_version')
        self.add_table('static_version')

    @staticmethod
    def read_data():
        path = str(settings.BASE_DIR.joinpath('datatable_examples', 'data', 'no_model.json'))
        with open(path) as json_file:
            return json.load(json_file)

    @staticmethod
    def _add_columns(table):
        table.add_columns(
            'id',
            'first_name',
            'last_name',
            'company_name',
            ColumnBase(column_name='seconds', field='seconds', render=[
                {'function': 'hhmm', 'column': 'seconds', 'var': '%1%'},
               ], column_defs={'className': 'dt-right'}),
        )
        table.add_plugin(ColumnTotals, {'seconds': {'sum': True}})

    def setup_ajax_version(self, table):
        self._add_columns(table)

    def setup_static_version(self, table):
        self._add_columns(table)
        table.table_data = self.read_data()

    @staticmethod
    def get_table_query(table, **kwargs):
        return NoModelData.read_data()

    def add_to_context(self, **kwargs):
        return {'description': (
            'Tables do not need a model — any list of dicts works; here both tables read the same '
            'JSON file. The left table fetches its rows with AJAX by returning the data from '
            '<code>get_table_query</code>; the right table is embedded in the page by assigning '
            '<code>table.table_data</code> instead. The <i>seconds</i> column is formatted hh:mm by '
            'a custom JavaScript render function loaded with the page.'
        )}


class DemoForm(forms.Form):

    tags = forms.MultipleChoiceField(widget=DataTableWidget(fields=['id', 'tag'], model=models.Tags))
    order = forms.CharField(
        widget=DataTableReorderWidget(model=models.Company, order_field='order', fields=['name'])
    )


class FormWidgets(ManualPage, FormView):
    template_name = 'datatable_examples/widget_example.html'
    form_class = DemoForm
    ajax_commands = ['datatable', 'button']
    page_title = 'Form Widgets'
    code_examples = [DemoForm, 'datatable_sort']

    def get_initial(self):
        return {'tags': [1]}

    def datatable_sort(self, **kwargs):
        form = self.get_form()
        widget = form.fields[kwargs['table_id'][3:]].widget
        reorder(widget.attrs['table_model'], widget.order_field, kwargs['sort'])
        return self.command_response('reload')

    def add_to_context(self, **kwargs):
        return {'description': (
            'Datatables as Django form widgets. <code>DataTableWidget</code> renders a multiple-'
            'choice field as a selectable table, and <code>DataTableReorderWidget</code> gives a '
            'drag-to-reorder table whose sort posts back to <code>datatable_sort</code> and is saved '
            'to the model\'s order field.'
        )}


class ReadOnlyCellColumn(DatatableColumn):

    def row_result(self, data_dict, page_results):
        result = self.default_row_result(data_dict, page_results)
        return json.dumps({'data': result, 'class': self.cell_options['class'], 'readOnly': True})

    def col_setup(self):
        self.field = 'name'
        self.column_defs['width'] = 400
        self.spreadsheet = {'editor': 'spreadsheets.custom_column', 'stripHTML': False}
        self.cell_options = {'class': 'text-secondary table-primary '}


class SpreadsheetPage(ManualPage, DatatableView):
    template_name = 'datatable_examples/spreadsheet.html'
    model = models.Company
    page_title = 'Spreadsheet'

    def setup_menu(self):
        super().setup_menu()
        self.add_menu('page_menu', 'buttons').add_items(
            MenuItem(ajax_command('send_spreadsheet', table_id='spreadsheetpage'),
                     'SEND DATA', MenuItem.AJAX_COMMAND),
            MenuItem(ajax_command('set_cell', table_id='spreadsheetpage', cell='C2',
                                  value={'data': '4', 'class': 'table-danger'}),
                     'SET CELL', MenuItem.AJAX_COMMAND),
            'spreadsheet_modal')

    def row_changed(self, data, row_no, column, **_kwargs):
        return self.command_response('message', text=f'Data {row_no}:{column} changed {data}')

    def setup_table(self, table):
        table.add_columns(
            '.id', ('name', {'width': 400}), ReadOnlyCellColumn(),
        )
        table.ajax_data = False
        table.max_records = 4
        table.table_options['hide_index'] = False
        table.table_options['on_change'] = 'row'  # could be whole
        table.spreadsheet_config = {
            'minSpareRows': 3,
            'nestedHeaders': [[{'title': 'Grouped Header', 'colspan': '3'}]]
        }
        table.datatable_template = 'datatables/spreadsheet.html'

    def button_spreadsheet(self, **kwargs):
        return self.command_response('message', text=kwargs['data'])

    def add_to_context(self, **kwargs):
        return {'description': (
            'Rendering a table with <code>datatables/spreadsheet.html</code> swaps DataTables.js for '
            'an editable JSpreadsheet grid built from the same column definitions. Cell edits post '
            'back to <code>row_changed</code>, <i>SEND DATA</i> posts the whole sheet to '
            '<code>button_spreadsheet</code>, and <i>SET CELL</i> shows the server updating a cell '
            'with the <code>set_cell</code> command. The third column is read-only with custom cell '
            'classes, and <i>Modal</i> opens a spreadsheet inside a django-modals form.'
        )}


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
        table.add_columns('id', ('name', {'width': 400}))
        table.datatable_template = 'datatables/spreadsheet.html'
        table.max_records = 10
        form.buttons = [self.submit(), form.cancel_button()]
        self.render_ = [HTML(table.render())]
        return self.render_

    def form_valid(self, form):
        self.add_command('close')
        return self.command_response('message', text=form.data['modal-sheet'])
