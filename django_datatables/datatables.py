import json
from inspect import isclass
from typing import TypeVar, Dict
from django.db import models
from django.urls import reverse
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.template.loader import render_to_string
from .detect_device import detect_device
from .columns import ColumnBase, DateColumn, ChoiceColumn, render_replace, BooleanColumn
from .model_def import DatatableModel
from .filters import DatatableFilter

KT = TypeVar('KT')
VT = TypeVar('VT')


def options_to_dict(options):
    return dict((x, y) for x, y in options)


DUMMY_ID = 999999


def row_link(url_name, column_id):
    if type(url_name) == tuple:
        url = reverse(url_name[0], args=[*url_name[1:]])
    else:
        if url_name.find('999999') == -1:
            url = reverse(url_name, args=[999999])
        else:
            url = url_name
    return [render_replace(column=column_id, html=url, var='999999')]


class DatatableTable:

    page_length = 100

    def __init__(self, table_id, model=None):
        self.columns = []
        self.table_id = table_id
        self.table_options: Dict[KT, VT] = {}

        self.ajax_data = True
        self.model = model

        # django query attributes
        self.filter = {}
        self.exclude = {}
        self.distinct = []
        self.max_records = None

        # javascript datatable attributes
        self.order_by = []
        self.js_filter_list = []
        self.plugins = []

        self.table_classes = ['display', 'compact', 'smalltext', 'table-sm', 'table', 'w-100']
        self.table_options['pageLength'] = self.page_length
        self.omit_columns = []

    def table_class(self):
        return ' '.join(self.table_classes)

    def column(self, column_name):
        return self.find_column(column_name)[0]

    def add_js_filters(self, name_or_template, column_ids, **kwargs):
        if type(column_ids) == str:
            column_ids = [column_ids]
        for c in column_ids:
            self.js_filter_list.append(DatatableFilter(name_or_template, self, column=self.find_column(c)[0], **kwargs))

    def js_filter(self, name_or_template, column_id, **kwargs):
        return DatatableFilter(name_or_template, self, column=self.find_column(column_id)[0], **kwargs)

    def add_plugin(self, plugin, *args, **kwargs):
        self.plugins.append(plugin(self, *args, **kwargs))

    def get_query(self, **_kwargs):
        annotations = {}
        for c in self.columns:
            if c.annotations:
                annotations.update(c.annotations)
        query = (self.model.objects.annotate(**annotations).filter(**self.filter)
                 .exclude(**self.exclude).values(*self.fields())
                 .order_by(*self.order_by))
        if self.distinct:
            query = query.distinct(*self.distinct)
        if self.max_records:
            query = query[:self.max_records]
        return query

    def sort(self, *columns):
        self.table_options['order'] = []
        for c in columns:
            sort_order = 'asc'
            if c[0] == '-':
                sort_order = 'desc'
                c = c[1:]
            self.table_options.setdefault('order', []).append([self.find_column(c)[1], sort_order])

    def row_color(self, column, *option_colors):
        self.table_options.setdefault('rowColor', []).append(
            {'colRef': column, 'values': {o[0]: o[1] for o in option_colors}})

    def add_column_options(self, column_names, options):
        if type(column_names) == str:
            column_names = [column_names]
        for c in self.columns:
            if c.column_name in column_names:
                c.setup_kwargs(options)

    def find_column(self, column_name, by_field=False):
        for n, c in enumerate(self.columns):
            if by_field and c.field == column_name:
                return c, n
            if c.column_name == column_name:
                return c, n

    @staticmethod
    def generate_column(column_setup, start_field, model_field, **kwargs):
        if isclass(column_setup):
            column = column_setup(**kwargs, column_name=column_setup.__name__)
        elif isinstance(column_setup, ColumnBase):
            return column_setup.get_class_instance(column_name=start_field, **kwargs)
        else:
            # create a column from model field
            field = start_field.split('__')[-1]
            if model_field:
                field_type = type(model_field)
                if field_type in [models.DateField, models.DateTimeField]:
                    # column.row_result = MethodType(format_date_time, column)
                    column = DateColumn(field=field)
                elif (field_type in [models.IntegerField, models.PositiveSmallIntegerField, models.PositiveIntegerField]
                      and len(model_field.choices) > 0):
                    column = ChoiceColumn(field=field, choices=model_field.choices)
                elif field_type == models.BooleanField:
                    column = BooleanColumn(field=field)
                else:
                    column = ColumnBase(field=field)
                column = column.get_class_instance(column_name=start_field, **kwargs)
                column.title = model_field.verbose_name.title()
            else:
                column = ColumnBase(field=field).get_class_instance(column_name=start_field, **kwargs)
            if isinstance(column_setup, dict):
                column.column_name = field
                column.setup_kwargs(column_setup)
        return column

    def create_columns(self, start_model, start_field, **kwargs):
        # Could get multiple columns from a definition in a model
        field_str, options = ColumnBase.extract_options(start_field)
        model, field, setup = DatatableModel.get_setup_data(start_model, field_str)
        if type(setup) != list:
            return [self.generate_column(setup, start_field, field,  **kwargs)]
        columns = []
        for s in setup:
            columns.append(self.generate_column(s, start_field, field, **kwargs))
        return columns

    def get_columns(self, column, **kwargs):
        if isinstance(column, str):
            if column in self.omit_columns:
                return []
            return self.create_columns(self.model, column, **kwargs)
        elif isinstance(column, ColumnBase):
            if column.column_name in self.omit_columns:
                return []
            return [column]
        else:
            return self.create_columns(self.model, column[0], **column[1])

    def add_columns(self, *columns, **kwargs):
        for c in columns:
            new_columns = self.get_columns(c, **kwargs)
            for add_col in new_columns:
                self.columns.append(add_col)

    def fields(self):
        fields = []
        for c in self.columns:
            if c.field and 'calculated' not in c.options:
                if isinstance(c.field, (tuple, list)):
                    for f in c.field:
                        if f not in fields:
                            fields.append(f)
                else:
                    if c.field not in fields:
                        fields.append(c.field)
        return fields

    def all_names(self):
        return [c.column_name for c in self.columns]

    def all_titles(self):
        return [str(c.title) for c in self.columns]

    def render(self):
        rendered_strings = []
        for p in self.plugins:
            rendered_strings.append(p.render())
        rendered_strings.append(render_to_string('datatables/table.html', {'datatable': self}))
        return ''.join(rendered_strings)

    def setup_column_id(self):
        if 'column_id' not in self.table_options:
            column_id = self.find_column('id', True)
            if column_id:
                self.table_options['column_id'] = column_id[1]
                return self.columns[column_id[1]]
        else:
            return self.columns[self.table_options['column_id']]

    def col_def_str(self):
        self.setup_column_id()
        options = dict(self.table_options)
        if not self.ajax_data:
            options['data'] = self.get_table_array(None, self.get_query())
        options['columnDefs'] = [dict({'targets': i, 'name': c.column_name}, **c.style())
                                 for i, c in enumerate(self.columns)]
        table_vars = {
            'field_ids': self.all_names(),
            'colOptions': [c.options for c in self.columns],
            'tableOptions': options,
        }
        col_def_str = json.dumps(table_vars, separators=(',', ':'))
        # legacy modifications to col_def_str
        # col_def_str = col_def_str.replace('"&', "")
        # col_def_str = col_def_str.replace('&"', "")
        return col_def_str

    def get_table_array(self, request, results):
        json_list = []
        page_results = {}
        for c in self.columns:
            c.setup_results(request, page_results)
        for data_dict in results:
            json_list.append([c.row_result(data_dict, page_results) for c in self.columns])
        return json_list

    def get_json(self, request, results):
        return_data = {'data': self.get_table_array(request, results)}
        return json.dumps(return_data, separators=(',', ':'), default=str)

    def refresh_row(self, request, row_id):
        id_column = self.setup_column_id()
        if id_column:
            self.filter[id_column.field] = int(row_id[1:])
            results = self.get_table_array(request, self.get_query())[0]
            commands = [{'command': 'refresh_row', 'row': row_id, 'data': results, 'table': self.table_id}]
            return HttpResponse(json.dumps(commands), content_type='application/json')

    def delete_row(self, _request, row_id):
        commands = [{'command': 'delete_row', 'row': row_id, 'table': self.table_id}]
        return HttpResponse(json.dumps(commands), content_type='application/json')


class DatatableView(TemplateView):
    model = None

    def __init__(self, *args, **kwargs):
        super(DatatableView, self).__init__(*args, **kwargs)
        self.tables = {}
        self.add_tables()

        self.dispatch_context = None

    def add_table(self, table_id, **kwargs):
        self.tables[table_id] = DatatableTable(table_id, **kwargs)

    def add_tables(self):
        self.add_table(type(self).__name__.lower(), model=self.model)

    def setup_tables(self, table_id=None):
        for t_id, table in self.tables.items():
            if not table_id or t_id == table_id:
                if t_id == type(self).__name__.lower():
                    self.setup_table(table)
                else:
                    getattr(self, 'setup_' + t_id)(table)

    def dispatch(self, request, *args, **kwargs):
        self.dispatch_context = detect_device(request)
        return super(DatatableView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.setup_tables()
        return super().get(request, *args, **kwargs)

    # def render_to_response(self, context, **response_kwargs):
    #    if self.template_name is None:
    #        return HttpResponse(self.table.javascript_setup())
    #    return super(DatatableView, self).render_to_response(context, **response_kwargs)

    # @staticmethod
    # def graph_data(**kwargs):
    #    return None
    @staticmethod
    def setup_table(table):
        pass

    @staticmethod
    def locked():
        return False

    @staticmethod
    def get_table_query(table, **kwargs):
        return table.get_query(**kwargs)

    def post(self, request, *args, **kwargs):

        if 'datatable-data' in request.GET:
            table = self.tables[request.POST['table_id']]
            self.setup_tables(table_id=table.table_id)
            results = self.get_table_query(table, **kwargs)
            if self.locked():
                secure_fields = [c.field for c in table.columns if c.options.get('secure')]
                if secure_fields:
                    for r in results:
                        for f in secure_fields:
                            data = r.get(f)
                            if data:
                                r[f] = '<i class="fas fa-key"></i>'
            return HttpResponse(table.get_json(request, results),
                                content_type='application/json')

        for t in ['row', 'column']:
            if 'datatable-' + t in request.GET:
                table = self.tables[request.POST['table_id']]
                self.setup_tables(table_id=table.table_id)
                if hasattr(self, t + '_' + request.POST['command']):
                    column_values = json.loads(request.POST[t])
                    extra_data = {k: request.POST[k] for k in request.POST if k != t}
                    return getattr(self, t + '_' + request.POST['command'])(request, column_values, table, extra_data)
        return None

    def sent_column(self, column_values, extra_data):
        pass
    """
    def get(self, request, *args, **kwargs):
        if request.GET.get('json', None) is not None:
            '''
            # ***************************************************
            # Uncomment for benchmarking SQL calls for datatables
            # ***************************************************
            a = getJson(self.table, self.post_table_json(**kwargs))
            context = self.get_context_data(**kwargs)
            self.template_name = 'blank.html'
            return self.render_to_response(context)
            '''
            return self.table_json(**kwargs)
        else:
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if len(self.tables) == 1:
            context['datatable'] = self.tables[list(self.tables.keys())[0]]
        else:
            context['datatables'] = self.tables
        context.update(self.add_to_context(**kwargs))
        return context

    def add_to_context(self, **kwargs):
        return {}


simple_table = {
    'dom': 't',
    'no_col_search': True,
    'nofooter': True,
    'pageLength': 400,
}
