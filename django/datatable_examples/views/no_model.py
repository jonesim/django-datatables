import json

from datatable_examples.views.menu import MainMenu
from django.conf import settings

from django_datatables.columns import ColumnBase
from django_datatables.datatables import DatatableView
from django_datatables.plugins.column_totals import ColumnTotals


class NoModelAjaxVersion(MainMenu, DatatableView):
    template_name = 'datatable_examples/no_model.html'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'first_name',
            'last_name',
            'company_name',
            ColumnBase(column_name='seconds', field='seconds', render=[
                {'function': 'hhmm', 'column': 'seconds', 'var': '%1%'},

               ], column_defs={'className': 'dt-right'}),
        )
        table.table_options['scrollX'] = True
        table.add_plugin(ColumnTotals, {'seconds': {'sum': True}})

    @staticmethod
    def get_table_query(table, **kwargs):
        path = str(settings.BASE_DIR.joinpath('datatable_examples', 'data', 'no_model.json'))
        with open(path) as json_file:
            data = json.load(json_file)
        return data

    def add_to_context(self, **kwargs):
        return {'description': '''
        This example gets its data from a json file instead of the database via AJAX
        '''}


class NoModelNonAjaxVersion(MainMenu, DatatableView):
    template_name = 'datatable_examples/no_model.html'

    def setup_table(self, table):
        table.add_columns(
            'id',
            'first_name',
            'last_name',
            'company_name',
            ColumnBase(column_name='seconds', field='seconds', render=[
                {'function': 'hhmm', 'column': 'seconds', 'var': '%1%'},

               ], column_defs={'className': 'dt-right'}),
        )
        table.table_options['scrollX'] = True
        table.add_plugin(ColumnTotals, {'seconds': {'sum': True}})

        table.table_data = self.table_data()

    def table_data(self):
        path = str(settings.BASE_DIR.joinpath('datatable_examples', 'data', 'no_model.json'))
        with open(path) as json_file:
            data = json.load(json_file)
        return data

    def add_to_context(self, **kwargs):
        return {'description': '''
        This example gets its data from a json file instead of the database 
        '''}