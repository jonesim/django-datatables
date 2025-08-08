from django_datatables.columns.column_base import ColumnBase


class DateColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            date = data[self.field].strftime('%d/%m/%Y')
            return date
        except AttributeError:
            return ""


class DateTimeColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            date = data[self.field].strftime('%d/%m/%Y')
            time_str = data[self.field].strftime('%H:%M')
            return date + ' ' + time_str
        except AttributeError:
            return ""
