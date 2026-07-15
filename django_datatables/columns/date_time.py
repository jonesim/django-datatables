import datetime

from django_datatables.columns.column_base import ColumnBase


class DateColumn(ColumnBase):

    date_str = '%d/%m/%Y'

    def get_date_format(self):
        # Hook: subclasses can return a per-user / locale strftime format string.
        return self.date_str

    def get_date_format_xl(self):
        # Hook: openpyxl number format matching get_date_format().
        return 'dd/mm/yyyy'

    def col_setup(self):
        self.date_str = self.get_date_format()

    def row_result(self, data, _page_data):
        try:
            return data[self.field].strftime(self.date_str)
        except AttributeError:
            return ""

    def excel(self, value):
        if value:
            return datetime.datetime.strptime(value, self.date_str).date()
        return ''

    def xl_style(self, cell):
        cell.number_format = self.get_date_format_xl()


class DateTimeColumn(DateColumn):

    def get_date_format_xl(self):
        return 'dd/mm/yyyy hh:mm'

    def row_result(self, data, _page_data):
        try:
            return data[self.field].strftime(self.date_str) + ' ' + data[self.field].strftime('%H:%M')
        except AttributeError:
            return ""

    def excel(self, value):
        if value:
            return datetime.datetime.strptime(value, self.date_str + ' %H:%M')
        return ''
