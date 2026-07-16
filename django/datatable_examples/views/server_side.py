from datatable_examples import models
from datatable_examples.views.base import ManualPage
from django_datatables.columns import ColumnLink, JsonBooleanColumn, ManyToManyColumn
from django_datatables.datatables import DatatableView
from django_datatables.downloads.excel_download import ExcelDownload


class ServerSidePagination(ExcelDownload, ManualPage, DatatableView):
    """
    Demonstrates server-side pagination for large datasets.

    Each page request is sent to the server; the database applies the
    filtering, ordering, and slicing rather than loading all rows at once.
    The global search box and column-header search boxes send their values
    to the server and are applied via ORM icontains queries.

    The Excel download button exports the full filtered dataset: the browser
    sends its last request state and the server rebuilds the queryset, so the
    current search, filters, and sort order all apply to the export.
    """
    model = models.Person
    server_side = True
    ajax_commands = ['row', 'column']
    page_title = 'Server-side Pagination & Search'

    def setup_menu(self):
        self.add_menu('menu', 'buttons').add_items(self.download_menu_item())
        super().setup_menu()

    def setup_table(self, table):
        table.add_columns(
            'id',
            ('first_name', {'title': 'First Name'}),
            ('surname', {'title': 'Surname'}),
            # A list-field ColumnLink (id -> URL, surname -> displayed text). Its header
            # search box and sorting work server-side automatically via search_field,
            # which defaults to the displayed field (surname).
            ColumnLink(column_name='person_link', title='Surname (link)',
                       field=['id', 'surname'], url_name='column_visibility'),
            ('company__name', {'title': 'Company'}),
            ('title_model', {'title': 'Title', 'no_col_search': True}),
            ('date_entered', {'title': 'Date Entered', 'no_col_search': True}),
        )
        # Fields searched by the global search box.
        table.search_fields = ['first_name', 'surname', 'company__name']
        # Default ordering.
        table.order_by = ['surname', 'first_name']
        # Server-side facet filters: selections become ORM WHERE clauses and
        # the count badges come from GROUP BY queries.
        table.add_js_filters('select2', 'company__name')
        table.add_js_filters('pivot', 'title_model')
        table.add_js_filters('date', 'date_entered')

    def add_to_context(self, **kwargs):
        return {'description': (
            'Setting <code>server_side = True</code> switches the table to server-side mode: each '
            'page, sort, and search request is handled by the database rather than loaded into the '
            'browser. Column-header search boxes and the global DataTables search input are applied '
            'as ORM <code>icontains</code> filters over <code>search_fields</code>. The filter blocks '
            'on the left are applied server-side: badge counts come from GROUP BY queries and are '
            'only recalculated when the filter or search state changes.'
        )}


class ServerSideTagFilter(ManualPage, DatatableView):
    """Server-side table with a tag filter on a ManyToManyColumn."""
    model = models.Company
    server_side = True
    page_title = 'Server-side Tag Filter'

    def setup_table(self, table):
        table.add_columns(
            ('id', {'column_defs': {'width': '30px'}}),
            'name',
            ManyToManyColumn(column_name='CompanyTags', field='tags__tag', model=models.Company,
                             html='<span class="badge badge-primary"> %1% </span>'),
        )
        table.search_fields = ['name']
        table.add_js_filters('tag', 'CompanyTags')

    def add_to_context(self, **kwargs):
        return {'description': (
            'Server-side tag filter on a many-to-many column. Each tag checkbox cycles through four '
            'states: neutral, include (rows with any included tag), required (rows with every '
            'required tag), and exclude. The selections are applied as ORM queries and the badge '
            'counts come from GROUP BY queries with distinct row counts. Compare with the client-side '
            'version on the <i>Tag Filter</i> page in the Filters chapter.'
        )}


class ServerSideTotalsFilter(ManualPage, DatatableView):
    """Server-side table with a totals filter summing a column per group."""
    model = models.Payment
    server_side = True
    page_title = 'Server-side Totals Filter'

    def setup_table(self, table):
        table.add_columns(
            ('id', {'column_defs': {'width': '30px'}}),
            ('company__name', {'title': 'Company'}),
            'date',
            'amount',
        )
        table.search_fields = ['company__name']
        table.add_js_filters('totals', 'company__name', sum_column='amount',
                             filter_title='Amount by Company')

    def add_to_context(self, **kwargs):
        return {'description': (
            'Server-side totals filter. The filter block behaves like a pivot filter but the '
            'Filtered / Total columns show <code>Sum(amount)</code> per company computed with '
            'GROUP BY queries instead of row counts.'
        )}


class ServerSideJsonColumn(ManualPage, DatatableView):
    """Server-side pivot filter on a column whose value lives in a JSON field key."""
    model = models.Person
    server_side = True
    page_title = 'Server-side JSON Column Filter'

    def setup_table(self, table):
        table.add_columns(
            ('id', {'column_defs': {'width': '30px'}}),
            ('first_name', {'title': 'First Name'}),
            ('surname', {'title': 'Surname'}),
            JsonBooleanColumn(column_name='newsletter', json_key='newsletter'),
        )
        table.search_fields = ['first_name', 'surname']
        # The column's Yes/No value is computed in row_result, so the ORM
        # path to the JSON key is passed explicitly and choices= maps the
        # database values (True / False / missing key) to the labels.
        table.add_js_filters('pivot', 'newsletter', field='options__newsletter',
                             choices={True: 'Yes', False: 'No', None: 'No'})

    def add_to_context(self, **kwargs):
        return {'description': (
            'Server-side pivot filter on a JSON-field key. The column renders '
            '<code>options[\'newsletter\']</code> as a tick or blank in <code>row_result</code>, so '
            'the filter is given the ORM path with <code>field=\'options__newsletter\'</code> and a '
            '<code>choices=</code> map that folds <code>True</code>, <code>False</code>, and a '
            'missing key into the Yes / No labels. Selections are applied as JSON key lookups and '
            'the badge counts come from a GROUP BY on the key transform.'
        )}
