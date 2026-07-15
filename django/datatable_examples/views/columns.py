from django.db.models import Count, Sum, Min

from datatable_examples import models
from datatable_examples.views.base import ManualPage
from django_datatables.column_visibility.mixins import ColumnVisibilityMixin
from django_datatables.columns import (ColumnBase, ColumnLink, CurrencyPenceColumn, DatatableColumn,
                                       ManyToManyColumn, SelectColumn)
from django_datatables.constants import HIDE_OMIT, HIDE_OPTIONAL
from django_datatables.datatables import DatatableView, HorizontalTable


class ColumnLinks(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Column Links'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'name',
            ColumnLink(column_name='view_company_1', field=['id', 'name'], url_name='column_visibility'),
            ColumnLink(column_name='view_company_2', link_ref_column='id', field='name',
                       url_name='column_visibility'),
            ColumnLink(column_name='view_company_icon', link_ref_column='id', url_name='column_visibility',
                       width='10px',
                       link_html='<button class="btn btn-sm btn-outline-dark">'
                                 '<i class="fas fa-building"></i></button>'),
            'company_link',  # ColumnLink declared on the model's Datatable class
        )

    def add_to_context(self, **kwargs):
        return {'description': (
            '<code>ColumnLink</code> renders a cell as a link to a named URL, with the row\'s id '
            'substituted into the path. The id can be part of the column\'s own <code>field</code> '
            'list or supplied by another column with <code>link_ref_column</code>, and '
            '<code>link_html</code> replaces the text with arbitrary HTML such as an icon button. '
            'Links here go to the <i>Column Visibility</i> page, which filters people by the chosen '
            'company. The last column is declared once on the model\'s inner <code>Datatable</code> '
            'class and reused by name.'
        )}


class TagColumns(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Tags & Badges (Many-to-Many)'

    class TagsExample(DatatableColumn):
        """Many-to-many rendered by hand: one query for all rows in setup_results."""

        def setup_results(self, request, all_results):
            tags = models.Tags.objects.values_list('company__id', 'id')
            tag_dict = {}
            for t in tags:
                tag_dict.setdefault(t[0], []).append(t[1])
            all_results['tags'] = tag_dict

        @staticmethod
        def proc_result(data_dict, page_results):
            return page_results['tags'].get(data_dict['id'], [])

        def col_setup(self):
            self.title = 'Custom column'
            self.row_result = self.proc_result
            self.options['render'] = [
                {'var': '%1%', 'html': '<span class="badge badge-primary"> %1% </span>',
                 'function': 'ReplaceLookup'},
            ]
            self.options['lookup'] = list(models.Tags.objects.values_list('id', 'tag'))

    def setup_table(self, table):
        coloured_lookup = [[t[0], [t[1], 'warning' if t[0] % 2 else 'danger']]
                           for t in models.Tags.objects.values_list('id', 'tag')]
        table.add_columns(
            'id',
            'name',
            'TagList',  # custom column declared on the model's Datatable class
            self.TagsExample(column_name='tags_custom'),
            ManyToManyColumn(column_name='CompanyTags', field='tags__tag', model=models.Company,
                             html='<span class="badge badge-primary"> %1% </span>'),
            ManyToManyColumn(column_name='Coloured', field='tags__tag', model=models.Company,
                             lookup=coloured_lookup,
                             render=[{'var': ['%1%', '%2%'], 'html': '<span class="badge badge-%2%"> %1% </span>',
                                      'function': 'ReplaceLookup'}]),
        )

    def add_to_context(self, **kwargs):
        return {'description': (
            'Four ways to show a many-to-many relation as badges. <code>ManyToManyColumn</code> is the '
            'one-liner: it aggregates the related values and wraps each in the supplied HTML, optionally '
            'through a <code>lookup</code> that can also carry extra data such as a colour. When more '
            'control is needed, a custom <code>DatatableColumn</code> collects the relation with a single '
            'query in <code>setup_results</code> and maps ids to labels client-side with a '
            '<code>ReplaceLookup</code> render — shown both declared on the model (<code>TagList</code>) and '
            'in the view (<code>tags_custom</code>). A tag column can also drive a filter — see '
            '<i>Tag Filter</i> in the Filters chapter.'
        )}


class ColumnVisibility(ColumnVisibilityMixin, ManualPage, DatatableView):
    model = models.Person
    page_title = 'Column Visibility'
    ajax_commands = ['row', 'column']

    def setup_table(self, table):
        table.edit_fields = ['company__name']
        table.edit_options = {'company__name': {'select2': True}}
        table.add_columns(
            SelectColumn(hidden=True),
            ('.id', {'options': {'initial_filter': {'1': False, '102': False}}}),
            ('first_name', {'hide_options': HIDE_OPTIONAL}),
            ('company__name', {'title': 'Company Name'}),
            ('company__company_link', {'hide_options': HIDE_OMIT}),
        )
        if 'pk' in self.kwargs:
            table.filter = {'company__id': self.kwargs['pk']}
        table.add_js_filters('select2', 'company__name')
        table.add_js_filters('pivot', 'id')
        table.add_js_filters('selected', 'SelectColumn')
        table.hidden_side_bar = True
        table.table_options['ajax_url'] = self.request.path
        table.show_column_modal = True

    def add_to_context(self, **kwargs):
        description = (
            '<code>ColumnVisibilityMixin</code> lets users choose and reorder the visible columns, with '
            'the layout saved per user. <code>show_column_modal</code> adds the column-picker button, '
            'and per-column <code>hide_options</code> control the behaviour: <code>HIDE_OPTIONAL</code> '
            'columns are hidden on small screens, <code>HIDE_OMIT</code> columns are dropped from the '
            'request entirely when hidden. <code>hidden_side_bar</code> collapses the filter side bar '
            'behind a toggle. When the URL contains a company id (as the links on the '
            '<i>Column Links</i> page do) the table is filtered to that company.'
        )
        if 'pk' in self.kwargs:
            return {'description': description,
                    'title': f'{self.page_title} — company {self.kwargs["pk"]}'}
        return {'description': description}


class Aggregations(ManualPage, DatatableView):
    model = models.Tally
    page_title = 'Aggregations'

    def setup_table(self, table):
        table.add_columns(
            ColumnBase(column_name='cars', field='cars', calculated=True, aggregations={'cars': Sum('cars')}),
            ColumnBase(column_name='vans_sum', field='vans_s', calculated=True,
                       aggregations={'vans_s': Sum('vans')}),
            ColumnBase(column_name='vans_min', field='vans_m', calculated=True,
                       aggregations={'vans_m': Min('vans')}),
        )

    def add_to_context(self, **kwargs):
        return {'description': (
            'Columns marked <code>calculated=True</code> with an <code>aggregations</code> dict collapse '
            'the whole queryset into aggregate values — here the sum of cars and the sum and minimum of '
            'vans across every tally row.'
        )}


class AggregationsHorizontal(ManualPage, DatatableView):
    template_name = 'datatable_examples/horizontal.html'
    model = models.Payment
    page_title = 'Aggregations (Horizontal)'

    def add_table(self, table_id, **kwargs):
        self.tables[table_id] = HorizontalTable(table_id, table_options=self.table_options,
                                                table_classes=self.table_classes, view=self, **kwargs)

    def setup_table(self, table):
        table.add_columns(
            CurrencyPenceColumn(column_name='amount', field='amount',
                                calculated=True, aggregations={'amount': Sum('amount')}),
        )

    def add_to_context(self, **kwargs):
        return {'description': (
            'The same aggregation idea rendered with a <code>HorizontalTable</code>: column titles run '
            'down the left and there is a single value column — a natural fit when the whole table '
            'reduces to a handful of aggregates. <code>CurrencyPenceColumn</code> formats the stored '
            'pence value as pounds.'
        )}
