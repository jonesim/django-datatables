import json

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


class LocaleCurrencyColumn(ColumnBase):
    """Currency column rendered client-side via the datatables 'currency' function.

    Values are stored in pennies by default (pass ``pennies=True`` for whole units). The currency
    and locale come from the ``currency_code`` / ``locale`` kwargs, falling back to the class
    defaults; a table-level ``currency_code`` attribute overrides when no ``currency_code`` kwarg
    is given. Subclasses can set ``default_currency_code`` / ``default_locale`` (e.g. from a site
    config) so callers need not pass them each time.
    """

    default_currency_code = 'GBP'
    default_locale = 'en_GB'

    def row_result(self, data, _page_data):
        if isinstance(self.field, list):
            try:
                return '{:.4f}'.format(data[self.field[0]] / self.divisor), data[self.field[1]]
            except (TypeError, KeyError):
                return
        else:
            try:
                return '{:.4f}'.format(data[self.field] / self.divisor)
            except (TypeError, KeyError):
                return

    def setup_kwargs(self, kwargs):
        super().setup_kwargs(kwargs)
        self.column_defs['className'] = 'dt-right'
        self.divisor = 1 if kwargs.get('pennies') else 100.0
        self.options['render'] = [{'function': 'currency',
                                   'column': self.column_name,
                                   'var': '%1%',
                                   'currency_code': kwargs.get('currency_code') or self.default_currency_code,
                                   'decimal_places': kwargs.get('decimal_places', 2),
                                   'locale': kwargs.get('locale') or self.default_locale}]

    def set_currency(self):
        if hasattr(self.table, 'currency_code'):
            self.options['render'][0]['currency_code'] = self.table.currency_code

    def col_setup(self):
        if 'currency_code' not in self.kwargs:
            self.set_currency()

    @staticmethod
    def excel(value):
        if value:
            return float(value)

    @staticmethod
    def xl_style(cell):
        cell.number_format = '#,##0.00_-'


class MultiCurrencyColumn(ColumnBase):
    """Currency column where each value carries its own currency: value is ``[amount, currency]``.

    Override ``get_symbols()`` to map a currency name to a symbol/prefix for Excel formatting.
    """

    default_currency_code = 'GBP'
    default_locale = 'en_GB'

    @classmethod
    def get_symbols(cls):
        # Hook: subclasses return {currency_name: symbol} used to format the Excel cells.
        return {}

    def row_result(self, data, _page_data):
        try:
            return data[self.field[0]] / 100, data[self.field[1]]
        except (TypeError, KeyError):
            return

    def setup_kwargs(self, kwargs):
        super().setup_kwargs(kwargs)
        self.column_defs['className'] = 'dt-right'
        self.divisor = 1 if kwargs.get('pennies') else 100.0
        self.options['render'] = [{'function': 'currency',
                                   'column': self.column_name,
                                   'var': '%1%',
                                   'multi_currency': True,
                                   'currency_code': kwargs.get('currency_code') or self.default_currency_code,
                                   'decimal_places': kwargs.get('decimal_places', 2),
                                   'locale': kwargs.get('locale') or self.default_locale}]

    @staticmethod
    def excel(value):
        return json.dumps(value)

    @classmethod
    def xl_style(cls, cell):
        try:
            v = json.loads(cell.value, strict=False)
            if v is None:
                cell.value = ''
            else:
                cell.value = v[0]
                cell.number_format = f'{cls.get_symbols().get(v[1], "")}#,##0.00_-'
        except TypeError:
            return
