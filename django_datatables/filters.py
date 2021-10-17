import inspect
import string
import random
from django.template.loader import render_to_string


class DatatableFilter:

    template_library = {
        'pivot': 'datatables/filter_blocks/pivot_filter.html',
        'tag': 'datatables/filter_blocks/tag_filter.html',
        'totals': 'datatables/filter_blocks/pivot_totals.html',
        'select2': 'datatables/filter_blocks/select2_filter.html',
        'date': 'datatables/filter_blocks/date_filter.html',
        'expand': 'datatables/filter_blocks/row_tree.html',
    }

    def __init__(self, name_or_template, datatable, column=None, collapsed=False, filter_title=None, html_id=None,
                 **kwargs):

        self.column = column
        self.datatable = datatable
        self.collapsed = collapsed
        self.kwargs = kwargs
        if 'sum_column' in kwargs:
            kwargs['sum_column'] = self.datatable.find_column(kwargs['sum_column'])[1]
        if html_id:
            self.html_id = html_id
        else:
            letters = string.ascii_lowercase
            self.html_id = ''.join(random.choice(letters) for _i in range(10))

        if filter_title:
            self.filter_title = filter_title
        elif column:
            self.filter_title = column.title
        else:
            self.filter_title = ''
        if not inspect.isclass(name_or_template):
            if name_or_template in self.template_library:
                self.template = self.template_library[name_or_template]
            else:
                self.template = name_or_template

    def get_context(self):
        context = {
            'html_id': self.html_id,
            'filter_title': self.filter_title,
            'table': self.datatable,
            'collapsed': self.collapsed,
            'kwargs': self.kwargs
        }
        if self.column:
            context['column_no'] = self.datatable.find_column(self.column.column_name)[1]
        return context

    def render(self):
        return render_to_string(self.template, self.get_context())


class PythonPivotFilter(DatatableFilter):

    template = 'datatables/filter_blocks/python_pivot_filter.html'

    def get_context(self):
        context = super().get_context()
        context['options'] = [o[1] for o in self.kwargs['filter_list']]
        return context
