import json

from ajax_helpers.mixins import ajax_method
from django_menus.menu import MenuItem

from datatable_examples import models
from datatable_examples.views.menu import MainMenu
from django_datatables.columns import SelectColumn
from django_datatables.datatables import DatatableView
from django_datatables.helpers import send_selected


class Selection(MainMenu, DatatableView):
    model = models.Company
    ajax_commands = ['column']
    menu_display = 'Selection'

    def setup_menu(self):
        super().setup_menu()
        self.add_menu('page_menu', 'buttons').add_items(
            (send_selected('selection', 'selected'), 'Send Selected Ids', MenuItem.JAVASCRIPT),
            ('stats()', 'States', MenuItem.JAVASCRIPT),

        )
    @ajax_method
    def selected(self, column_data, table_id):
        selection = json.loads(column_data)
        print(selection)
        return self.command_response('message', text=f'You sent {len(selection)} selected ids from table id {table_id}')

    def setup_table(self, table):
        table.add_columns(
            SelectColumn(hidden=True),
            'id',
            'name'
        )
        table.add_js_filters('datatables/filter_blocks/selected_filter.html', 'SelectColumn')
