from django.db.models import ExpressionWrapper, F, FloatField

from datatable_examples import models
from datatable_examples.views.base import ManualPage
from django_datatables.columns import ColumnBase
from django_datatables.datatables import DatatableView
from django_datatables.helpers import render_replace
from django_datatables.plugins.column_totals import ColumnTotals
from django_datatables.plugins.reorder import Reorder
from django_datatables.plugins.save_filters import add_save_filters
from django_datatables.reorder_datatable import ReorderDatatableView


class ColumnTotalsPage(ManualPage, DatatableView):
    model = models.Tally
    page_title = 'Column Totals'

    @staticmethod
    def percentage(_column, data_dict, _page_results):
        number = data_dict.get(_column.field)
        if number is None:
            return ''
        else:
            number = f'{number:.1f}'
        if '.' in number:
            return number.rstrip('0').rstrip('.')
        else:
            return number

    def setup_table(self, table):
        total_vehicles_ew = ExpressionWrapper(F('cars') + F('vans'), output_field=FloatField())
        percentage_that_are_vans_ew = ExpressionWrapper(F('vans') * 100.0 / F('total_vehicles'),
                                                        output_field=FloatField())
        percentage_that_are_cars_ew = ExpressionWrapper(F('cars') * 100.0 / F('total_vehicles'),
                                                        output_field=FloatField())

        table.add_columns(
            'id',
            'cars',
            'vans',
            ColumnBase(column_name='total_vehicles',
                       field='total_vehicles',
                       annotations={'total_vehicles': total_vehicles_ew}),
            ColumnBase(column_name='percentage_that_are_vans',
                       field='percentage_that_are_vans',
                       annotations={'percentage_that_are_vans': percentage_that_are_vans_ew},
                       row_result=self.percentage,
                       render=[render_replace(html='%1%&thinsp;%', column='percentage_that_are_vans')],
                       column_defs={'className': 'dt-right'}
                       ),
            ColumnBase(column_name='percentage_that_are_cars',
                       field='percentage_that_are_cars',
                       annotations={'percentage_that_are_cars': percentage_that_are_cars_ew},
                       row_result=self.percentage,
                       render=[render_replace(html='%1%&thinsp;%', column='percentage_that_are_cars')],
                       column_defs={'className': 'dt-right'}
                       )
        )
        table.add_plugin(ColumnTotals, {'id': {'css_class': 'text-danger', 'text': 'Total'},
                                        'cars': {'sum': 'over1000'},
                                        'vans': {'sum': True},
                                        'total_vehicles': {'sum': True},
                                        'percentage_that_are_vans': {'css_class': 'dt-right',
                                                                     'sum': 'percentage',
                                                                     'denominator': 'total_vehicles',
                                                                     'numerator': 'vans',
                                                                     'decimal_places': 1},
                                        'percentage_that_are_cars': {'css_class': 'dt-right',
                                                                     'sum': 'percentage',
                                                                     'denominator': 'total_vehicles',
                                                                     'numerator': 'cars',
                                                                     'decimal_places': 1}
                                        },
                         template='datatable_examples/add_sum_calc.html')

    def add_to_context(self, **kwargs):
        return {'description': (
            'The <code>ColumnTotals</code> plugin adds a footer row that recalculates as the table is '
            'filtered. Each column chooses how to total: a plain <code>sum</code>, a weighted '
            '<code>percentage</code> (numerator / denominator sums, so the footer percentage is exact '
            'rather than an average of row percentages), fixed <code>text</code>, or a custom '
            'JavaScript formatting function — the <i>cars</i> total is defined in an overriding '
            'template and turns red above 1000. The percentage columns are built from '
            '<code>ExpressionWrapper</code> annotations.'
        )}


class RowReorder(ManualPage, ReorderDatatableView):
    template_name = 'datatable_examples/plain_table.html'
    model = models.Company
    order_field = 'order'
    page_title = 'Row Reorder'

    @staticmethod
    def setup_table(table):
        table.add_columns('name')
        table.add_plugin(Reorder)

    def add_to_context(self, **kwargs):
        return {'description': (
            'Drag-and-drop row ordering. <code>ReorderDatatableView</code> with an '
            '<code>order_field</code> saves the new position back to the model when a row is dropped; '
            'the <code>Reorder</code> plugin supplies the drag handle column.'
        )}


class SaveFilters(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Save Filters'

    def setup_table(self, table):
        table.add_columns(
            'id',
            'name',
            'TagList',
        )
        table.add_js_filters('tag', 'TagList')
        add_save_filters(table, self.request.user)

    def add_to_context(self, **kwargs):
        return {'description': (
            '<code>add_save_filters</code> adds a block that saves the table\'s current state — '
            'filters, search, ordering — as a named <code>SavedState</code> record for the logged-in '
            'user, with a dropdown to restore any saved state later. Set some tag filters, save them '
            'under a name, change them, then load the saved state back.'
        )}
