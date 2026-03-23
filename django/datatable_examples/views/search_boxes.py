from datatable_examples import models
from datatable_examples.views.menu import MainMenu

from django_datatables.columns import ColumnBase
from django_datatables.datatables import DatatableView


class SearchBoxes(MainMenu, DatatableView):
    model = models.Company

    def setup_table(self, table):
        table.add_columns(
            'name',
            ColumnBase(column_name='dissolved',
                       field='dissolved',
                       col_search_select=[['true', 'True'], ['false', 'False']]),
            ColumnBase(column_name='order', field='order', no_col_search=True)

        )

    def add_to_context(self, **kwargs):
        context = {'description': '''
        This is example shows different types of search boxes.
        '''}

        if 'pk' in self.kwargs:
            context['title'] = type(self).__name__ + ' ' + ' pk:' + str(self.kwargs['pk'])
        else:
            context['title'] = type(self).__name__
        return context
