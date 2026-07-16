import json

from django_datatables.columns.column_base import ColumnBase


class CurrencyColumn(ColumnBase):
    """Right aligned currency rendered server-side to two decimal places.

    ``divisor`` scales the stored value before rendering; the default of 1 renders a value
    already held in whole units. See ``CurrencyPenceColumn`` for a value held in pennies.
    """

    divisor = 1

    def row_result(self, data, _page_data):
        try:
            return '{:.2f}'.format(data[self.field] / self.divisor)
        except (KeyError, TypeError):
            return

    def setup_kwargs(self, kwargs):
        super().setup_kwargs(kwargs)
        self.column_defs['className'] = 'dt-right'


class CurrencyPenceColumn(CurrencyColumn):
    """CurrencyColumn for a value stored in pennies."""

    divisor = 100.0


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
    multi_currency = False

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
        render = {'function': 'currency',
                  'column': self.column_name,
                  'var': '%1%',
                  'currency_code': kwargs.get('currency_code') or self.default_currency_code,
                  'decimal_places': kwargs.get('decimal_places', 2),
                  'locale': kwargs.get('locale') or self.default_locale}
        if self.multi_currency:
            render['multi_currency'] = True
        self.options['render'] = [render]

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


class MultiCurrencyColumn(LocaleCurrencyColumn):
    """Currency column where each value carries its own currency: value is ``[amount, currency]``.

    Override ``get_symbols()`` to map a currency name to a symbol/prefix for Excel formatting.
    """

    multi_currency = True

    @classmethod
    def get_symbols(cls):
        # Hook: subclasses return {currency_name: symbol} used to format the Excel cells.
        return {}

    def row_result(self, data, _page_data):
        # Unlike LocaleCurrencyColumn the amount is left unformatted, so that excel()/xl_style()
        # can round-trip it as a number and apply the per-currency number format.
        try:
            return data[self.field[0]] / self.divisor, data[self.field[1]]
        except (TypeError, KeyError):
            return

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
