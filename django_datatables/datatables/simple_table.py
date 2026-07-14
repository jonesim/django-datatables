from django.utils.safestring import mark_safe
from html_classes.html import HtmlTable

from django_datatables.datatables.datatable_table import DatatableTable, DatatableExcludedRow


class SimpleTable(DatatableTable):
    """
    Uses the same column definitions as DatatableTable but renders as a plain HTML
    table rather than a DataTables JS table. Suitable for search results and any
    view where server-rendered pagination is preferred over client-side JS.

    Usage in a view::

        def add_tables(self):
            self.add_table('results', model=MyModel, table_class=SimpleTable)

        def setup_table(self, table):
            table.add_columns('name', 'date', ColumnLink(column_name='view', field='name', url_name='my_view'))

    In the template::

        {{ datatable.render }}
    """

    table_classes = ['table', 'table-sm', 'table-hover']

    def render_rows(self, request, results):
        result_processes = self.get_result_processes()
        for p in result_processes:
            p.setup_results(request, self.page_results)
        for c in self.columns:
            c.setup_results(request, self.page_results)
        rows = []
        for data_dict in results:
            try:
                rows.append([c.html_result(data_dict, self.page_results) for c in self.columns])
            except DatatableExcludedRow:
                pass
        return rows

    def render(self):
        request = self.view.request if self.view else None
        results = self.get_query()
        rows = self.render_rows(request, results)
        data = [self.all_titles()] + rows
        return HtmlTable(data=data, headers=1, grouped=True, css_classes=self.table_class()).render()
