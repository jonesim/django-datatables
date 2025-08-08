from django_datatables.columns.column_base import ColumnBase


class CurrencyPenceColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            return '{:.2f}'.format(data[self.field] / 100.0)
        except (KeyError, TypeError):
            return

    def setup_kwargs(self, kwargs):
        super().setup_kwargs(kwargs)
        self.column_defs = {'className': 'dt-right'}


class CurrencyColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            return '{:.2f}'.format(data[self.field])
        except (KeyError, TypeError):
            return

    def setup_kwargs(self, kwargs):
        super().setup_kwargs(kwargs)
        self.column_defs = {'className': 'dt-right'}
