import inspect
import json
import string
import random
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class DatatableFilter:

    template_library = {
        'pivot': 'datatables/filter_blocks/pivot_filter.html',
        'tag': 'datatables/filter_blocks/tag_filter.html',
        'totals': 'datatables/filter_blocks/pivot_totals.html',
        'select2': 'datatables/filter_blocks/select2_filter.html',
        'date': 'datatables/filter_blocks/date_filter.html',
        'expand': 'datatables/filter_blocks/row_tree.html',
        'selected': 'datatables/filter_blocks/selected_filter.html',
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

    def column_titles(self):
        """Resolve the ``columns`` kwarg to a list of (title, column_name, column_no) tuples."""
        result = []
        for c in self.kwargs['columns']:
            column, column_no = self.datatable.find_column(c)
            result.append((column.title, column.column_name, column_no))
        return result

    def render(self):
        return render_to_string(self.template, self.get_context())


class PythonPivotFilter(DatatableFilter):
    """Pivot filter with a fixed option list defined in Python.

    The checkboxes are rendered server-side from ``filter_list`` instead of
    being derived from the table's distinct column values::

        table.add_js_filters(PythonPivotFilter, 'status',
                             filter_list=[('Active', 'active'), ('Other', 'other')])

    ``filter_list`` is a list of ``(label, value)`` pairs.  Row values not in
    the list are grouped under the ``'other'`` value when one is defined and
    are otherwise left unfiltered.  Filtering and the count badges still run
    client-side, so this is for standard (non server-side) tables only.
    """

    template = 'datatables/filter_blocks/python_pivot_filter.html'

    def get_context(self):
        context = super().get_context()
        option_values = json.dumps([str(o[1]) for o in self.kwargs['filter_list']])
        context['options'] = mark_safe(option_values.replace('<', '\\u003C'))
        return context
