from datatable_examples import models
from datatable_examples.views.menu import MainMenu
from django.db.models import Sum, Min

from django_datatables.columns import ColumnBase, CurrencyPenceColumn
from django_datatables.datatables import DatatableView, HorizontalTable


class ExampleAggregations(MainMenu, DatatableView):
    model = models.Tally

    def setup_table(self, table):
        table.add_columns(
            ColumnBase(column_name='cars', field='cars', calculated=True, aggregations={'cars': Sum('cars')}),
            ColumnBase(column_name='vans_sum', field='vans_s', calculated=True, aggregations={'vans_s': Sum('vans')}),
            ColumnBase(column_name='vans_min', field='vans_m', calculated=True, aggregations={'vans_m': Min('vans')}),
        )

    def add_to_context(self, **kwargs):
        return {'description': '''
        This example shows aggregations from the tally model
        '''}


class ExampleAggregationsHorizontal(MainMenu, DatatableView):
    template_name = 'datatable_examples/horizontal.html'
    model = models.Payment

    def add_table(self, table_id, **kwargs):
        self.tables[table_id] = HorizontalTable(table_id, table_options=self.table_options,
                                                table_classes=self.table_classes, view=self, **kwargs)

    def setup_table(self, table):
        table.add_columns(
            CurrencyPenceColumn(column_name='amount', field='amount',
                                calculated=True, aggregations={'amount': Sum('amount')}),
        )

    def add_to_context(self, **kwargs):
        return {'description': '''
        This example shows aggregations from the payment model
        '''}