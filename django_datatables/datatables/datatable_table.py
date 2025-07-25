import json
from inspect import isclass
from typing import TypeVar, Dict

from ajax_helpers.utils import random_string
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from django_datatables.datatables.column_initialiser import ColumnInitialisor
from django_datatables.datatables.datatable_error import DatatableError
from django_datatables.filters import DatatableFilter

KT = TypeVar('KT')
VT = TypeVar('VT')


class DatatableExcludedRow(Exception):
    pass


class DatatableTable:
    datatable_template = 'datatables/table.html'
    column_initialisor_cls = ColumnInitialisor

    edit_options = {}
    edit_fields = []
    query_manager = 'objects'

    def __init__(self, table_id=None, model=None, table_options=None, table_classes=None, view=None, **kwargs):
        self.columns = []
        self.table_id = table_id if table_id else random_string()
        self.table_options: Dict[KT, VT] = {'pageLength': 100}
        self.view = view
        if table_options:
            self.table_options.update(table_options)

        self.ajax_data = True
        self.table_data = None
        self.model = model
        self.page_results = {}
        self.results_limited = False

        # django query attributes
        self.initial_filter = {}
        self.initial_values = []
        self.filter = {}
        self.exclude = {}
        self.distinct = None
        self.max_records = None

        # javascript datatable attributes
        self.order_by = []
        self.js_filter_list = []
        self.plugins = []
        self.omit_columns = []

        self.kwargs = kwargs
        self.spreadsheet_config = {}

        self.cache_data = False
        self.cached_linked_tables = []
        self.cache_expiry = None
        self.ajax_commands = []

        if table_classes:
            self.table_classes = table_classes
        else:
            self.table_classes = ['display', 'compact', 'smalltext', 'table-sm', 'table', 'w-100']

    def table_class(self):
        return ' '.join(self.table_classes)

    def column(self, column_name):
        return self.find_column(column_name)[0]

    def add_js_filters(self, name_or_template, *column_ids, filter_class=DatatableFilter, **kwargs):
        if isclass(name_or_template):
            filter_class = name_or_template
        if column_ids:
            if isinstance(column_ids[0], (list, tuple)):
                column_ids = column_ids[0]
            for c in column_ids:
                self.js_filter_list.append(filter_class(name_or_template, self, column=self.find_column(c)[0],
                                                        **kwargs))
        else:
            self.js_filter_list.append(filter_class(name_or_template, self, **kwargs))

    def js_filter(self, name_or_template, column_id, **kwargs):
        return DatatableFilter(name_or_template, self, column=self.find_column(column_id)[0], **kwargs)

    def add_plugin(self, plugin, *args, **kwargs):
        self.plugins.append(plugin(self, *args, **kwargs))

    @staticmethod
    def extra_filters(query):
        return query

    @staticmethod
    def view_filter(query, table):
        return query

    def get_query(self, **_kwargs):
        annotations = {}
        annotations_value = {}
        aggregations = {}
        for c in self.columns:
            if c.get_annotations(**self.kwargs):
                annotations.update(c.get_annotations(**self.kwargs))
            if c.annotations_value:
                annotations_value.update(c.annotations_value)
            if c.aggregations:
                aggregations.update(c.aggregations)
        query = getattr(self.model, self.query_manager)
        # Use initial values to group_by for annotations
        if self.initial_values:
            query = query.values(*self.initial_values)
        if self.initial_filter:
            query = (query.filter(self.initial_filter) if isinstance(self.initial_filter, models.Q)
                     else query.filter(**self.initial_filter))
        if annotations_value:
            query = query.annotate(**annotations_value).values(*[f for f in annotations_value])
        query = query.annotate(**annotations).exclude(**self.exclude).values(*self.fields()).order_by(*self.order_by)
        if isinstance(self.filter, models.Q):
            query = query.filter(self.filter)
        else:
            query = query.filter(**self.filter)
        if self.distinct is not None:
            query = query.distinct(*self.distinct)
        if self.max_records:
            query = query[:self.max_records + 1]
        query = self.extra_filters(query=query)
        query = self.view_filter(query, self)
        if aggregations:
            aggregations_data = {}
            for column_name, column_config in aggregations.items():
                aggregations_data.update(query.aggregate(**{column_name: column_config}))
            query = [aggregations_data]

        return query

    def sort(self, *columns):
        self.table_options['order'] = []
        for c in columns:
            sort_order = 'asc'
            if c[0] == '-':
                sort_order = 'desc'
                c = c[1:]
            self.table_options.setdefault('order', []).append([self.find_column(c)[1], sort_order])

    def add_column_options(self, column_names, options):
        if type(column_names) == str:
            column_names = [column_names]
        for c in self.columns:
            if c.column_name in column_names:
                c.setup_kwargs(options)

    def find_column(self, column_name, by_field=False):
        if not by_field:
            for n, c in enumerate(self.columns):
                if c.column_name == column_name:
                    return c, n
        for n, c in enumerate(self.columns):
            if c.field == column_name:
                return c, n
        for n, c in enumerate(self.columns):
            if c.column_name.split('/')[-1] == column_name:
                return c, n
        raise DatatableError('Unable to find column ' + column_name)

    def add_columns(self, *columns):
        for c in columns:
            new_columns = self.column_initialisor_cls(self.model, c, table=self).get_columns()
            self.columns += [nc for nc in new_columns if nc.enabled]
        return self

    def fields(self):

        def add_fields(current_fields, new_fields):
            if isinstance(new_fields, (tuple, list)):
                current_fields.update(new_fields)
            else:
                current_fields.add(new_fields)

        fields = set()
        for p in self.get_result_processes():
            if hasattr(p, 'field'):
                add_fields(fields, p.field)
        for c in self.columns:
            if c.field and 'calculated' not in c.options:
                add_fields(fields, c.field)
        return fields

    def all_names(self):
        return [c.column_name for c in self.columns]

    def all_titles(self):
        return [mark_safe(str(c.title) + ('' if not c.popover else c.popover_html.format(c.popover)))
                for c in self.columns]

    def render(self):
        rendered_strings = []
        for p in self.plugins:
            rendered_strings.append(p.render())
        rendered_strings.append(render_to_string(self.datatable_template, {'datatable': self}))
        return mark_safe(''.join(rendered_strings))

    def setup_column_id(self):
        if 'column_id' not in self.table_options:
            try:
                self.table_options['column_id'] = self.find_column('id', True)[1]
                return self.columns[self.table_options['column_id']]
            except DatatableError:
                pass
        else:
            return self.columns[self.table_options['column_id']]

    @property
    def local_storage_key(self):
        view = self.view.__class__.__name__ if self.view else 'NoView'
        return f'Datatable_{view}_{self.table_id}'

    def col_def_str(self):
        self.setup_column_id()
        options = dict(self.table_options)
        if self.table_data is not None:
            request = getattr(self.view, 'request', None)
            options['data'] = self.get_table_array(request, self.table_data)
        elif not self.ajax_data:
            request = getattr(self.view, 'request', None)
            options['data'] = self.get_table_array(request, self.get_query())

        options['columnDefs'] = [dict({'targets': i, 'name': c.column_name}, **c.style())
                                 for i, c in enumerate(self.columns)]
        table_vars = {
            'field_ids': self.all_names(),
            'colOptions': [c.options for c in self.columns],
            'tableOptions': options,
            'local_storage_key': self.local_storage_key,
        }
        if request and hasattr(request, 'session'):
            table_vars['session_id'] = getattr(request.session, 'session_key', '-')
        col_def_str = json.dumps(table_vars, separators=(',', ':'))
        # legacy modifications to col_def_str
        # col_def_str = col_def_str.replace('"&', "")
        # col_def_str = col_def_str.replace('&"', "")
        return col_def_str

    def table_json_data(self):
        request = getattr(self.view, 'request', None)
        return json.dumps(self.get_table_array(request, self.get_query()))

    def spreadsheet_params(self):
        params = [f'columns: [{",".join([c.spreadsheet_init() for c in self.columns])}]',
                  f'data: {self.table_json_data()}',
        ]
        if self.table_options.get('on_change') == 'row':
            params.append('onchange: spreadsheets.spreadsheet_change')
        elif self.table_options.get('on_change') == 'whole':
            params.append('onchange: spreadsheets.spreadsheet_change_whole')

        for k, v in self.spreadsheet_config.items():
            if isinstance(v, bool):
                params.append(f'{k}: {str(v).lower()}')
            elif isinstance(v, (dict, list)):
                params.append(f'{k}: {json.dumps(v)}')
            elif isinstance(v, int):
                params.append(f'{k}: {v}')
            else:
                params.append(f'{k}: "{v}"')
        return mark_safe(f"{{{','.join(params)}}}")

    def spreadsheet_options(self):
        commands = [f'sheet.hideColumn({c_no})' for c_no, c in enumerate(self.columns) if c.options.get('hidden')]
        if self.table_options.get('hide_index'):
            commands.append('sheet.hideIndex()')
        return ';'.join(commands)

    def get_result_processes(self):
        result_processes = {}
        for c in self.columns:
            result_processes.update(c.result_processes)
        return result_processes.values()

    def get_table_array(self, request, results):
        result_processes = self.get_result_processes()
        for p in result_processes:
            p.setup_results(request, self.page_results)
        for c in self.columns:
            c.setup_results(request, self.page_results)
        results_list = []
        if self.max_records and len(results) > self.max_records:
            results = results[:self.max_records]
            self.results_limited = True
            if hasattr(self.view, 'max_records_warning'):
                self.view.max_records_warning(self)
        for data_dict in results:
            try:
                for p in result_processes:
                    p.row_result(data_dict, self.page_results)
                results_list.append([c.row_result(data_dict, self.page_results) for c in self.columns])
            except DatatableExcludedRow:
                pass
        return results_list

    def get_json(self, request, results):
        return_data = {'data': self.get_table_array(request, results)}
        if self.ajax_commands:
            return_data['ajax_commands'] = self.ajax_commands
        return json.dumps(return_data, separators=(',', ':'), default=str)

    def refresh_row_command(self, request, row_id):
        id_column = self.setup_column_id()
        if id_column:
            self.filter[id_column.field] = int(row_id[1:])
            results = self.get_table_array(request, self.get_query())[0]
            return {'function': 'refresh_row', 'row_no': row_id, 'data': results, 'table_id': self.table_id}

    def refresh_row(self, request, row_id):
        return JsonResponse([self.refresh_row_command(request, row_id)], safe=False)

    def delete_row(self, _request, row_id):
        commands = [{'command': 'delete_row', 'row': row_id, 'table': self.table_id}]
        return HttpResponse(json.dumps(commands), content_type='application/json')

    def remove_columns(self, *column_names):
        for n in column_names:
            del self.columns[self.find_column(n)[1]]


class HorizontalTable(DatatableTable):

    datatable_template = 'datatables/horizontal_table.html'

    def __init__(self, *args, **kwargs):
        pk = kwargs.pop('pk', None)
        kwargs.setdefault('table_classes', ['table', 'table-sm', 'bg-light', 'w-100'])
        super().__init__(*args, **kwargs)
        if pk:
            self.filter['pk'] = pk

    def model_table_setup(self):
        return mark_safe(json.dumps({'initsetup': json.loads(self.col_def_str()),
                                     'data': self.get_table_array(self.kwargs.get('request'), self.get_query()),
                                     'row_titles': self.all_titles(),
                                     'table_id': self.table_id,
                                     }))
