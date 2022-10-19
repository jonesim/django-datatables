import json
from inspect import isclass
from typing import TypeVar, Dict
from ajax_helpers.utils import random_string, is_ajax
from django.db import models
from django.http.response import HttpResponseBase
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from .detect_device import detect_device
from .columns import ColumnBase, DateColumn, ChoiceColumn, BooleanColumn, CallableColumn
from .model_def import DatatableModel
from .filters import DatatableFilter
from .models import SavedState
KT = TypeVar('KT')
VT = TypeVar('VT')


class DatatableError(Exception):
    pass


class DatatableExcludedRow(Exception):
    pass


class ColumnInitialisor:

    def __init__(self, start_model, path, field_prefix='', name_prefix='', **kwargs):
        self.start_model = start_model
        self.django_field = None
        self.setup = None
        self.model = None
        if type(path) == tuple:
            kwargs.update(path[1])
            path = path[0]
        self.kwargs = kwargs
        self.columns = []
        self.callable = False
        self.next_prefix = ''
        explicit_name = False
        if isclass(path):
            self.setup = path
            self.next_prefix = field_prefix
            self.kwargs['column_name'] = path.__name__
        elif isinstance(path, ColumnBase):
            self.setup = path
            if not hasattr(path, 'column_name'):
                self.kwargs['column_name'] = type(path).__name__
        elif isinstance(path, str):
            self.path, options = ColumnBase.extract_options(path)
            self.path = field_prefix + self.path
            self.kwargs.update(options)
            if start_model is not None:
                self.model, self.django_field, self.setup = DatatableModel.get_setup_data(start_model, self.path)
            if 'column_name' in self.kwargs:
                explicit_name = True
            else:
                self.kwargs['column_name'] = path

            if '__' in self.path:
                split_path = self.path.split('__')
                self.field = split_path[-1]
                self.next_prefix = '__'.join(split_path[:-1]) + '__'
            else:
                self.field = self.path
            self.callable = callable(getattr(self.model, self.field, None))
        else:
            raise DatatableError('Unknown type in columns ' + str(path))

        if 'column_name' in kwargs and name_prefix and not explicit_name:
            self.kwargs['column_name'] = f'{name_prefix}/{field_prefix}{self.kwargs["column_name"]}'

    def get_columns(self):
        self.kwargs['model'] = self.model
        self.kwargs['model_path'] = self.next_prefix
        if isclass(self.setup):
            self.columns.append(self.setup(**self.kwargs))
        elif isinstance(self.setup, ColumnBase):
            if self.setup.initialised:
                if 'table' in self.kwargs:
                    self.setup.table = self.kwargs['table']
                self.columns.append(self.setup)
            else:
                self.columns.append(self.setup.get_class_instance(**self.kwargs))
        elif isinstance(self.setup, list):
            del self.kwargs['column_name']
            for c in self.setup:
                self.columns += ColumnInitialisor(start_model=self.start_model, path=c, field_prefix=self.next_prefix,
                                                  name_prefix=self.field, **self.kwargs).get_columns()
        elif self.callable:
            if self.setup is None:
                self.setup = {}
            self.columns.append(CallableColumn(field=self.field, **self.kwargs, **self.setup))
        else:
            self.kwargs['field'] = self.field
            if isinstance(self.setup, dict):
                self.kwargs.update(self.setup)
            if self.django_field:
                self.add_django_field_column()
            else:
                self.columns.append(ColumnBase(**self.kwargs))
        return self.columns

    def add_django_field_column(self):
        if 'title' not in self.kwargs:
            self.kwargs['title'] = self.django_field.verbose_name.title()
        if isinstance(self.django_field, (models.DateField, models.DateTimeField)):
            self.columns.append(DateColumn(**self.kwargs))
        elif (isinstance(self.django_field,
                         (models.IntegerField, models.PositiveSmallIntegerField, models.PositiveIntegerField))
              and self.django_field.choices is not None and len(self.django_field.choices) > 0):
            self.columns.append(ChoiceColumn(choices=self.django_field.choices, **self.kwargs))
        elif isinstance(self.django_field, models.BooleanField):
            self.columns.append(BooleanColumn(**self.kwargs))
        else:
            self.columns.append(ColumnBase(**self.kwargs))


class DatatableTable:
    datatable_template = 'datatables/table.html'

    edit_options = {}
    edit_fields = []

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

        self.cache_data = False
        self.cached_linked_tables = []
        self.cache_expiry = None

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
        query = self.model.objects
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
            query = query[:self.max_records]
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
            new_columns = ColumnInitialisor(self.model, c, table=self).get_columns()
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

    def col_def_str(self):
        self.setup_column_id()
        options = dict(self.table_options)
        if self.table_data:
            options['data'] = self.get_table_array(None, self.table_data)
        elif not self.ajax_data:
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


class DatatableView(TemplateView):
    model = None
    table_classes = None
    table_options = None
    ajax_commands = ['row']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tables = {}
        self.dispatch_context = None

    def row_edit(self, **kwargs):
        row_data = json.loads(kwargs.pop('row_data'))
        table = self.tables[kwargs['table_id']]
        row_object = table.model.objects.get(pk=kwargs['row_no'][1:])
        self.setup_table(table)
        table.columns[kwargs['changed'][0]].alter_object(row_object, row_data[kwargs['changed'][0]])
        return table.refresh_row(self.request, kwargs['row_no'])

    def row_refresh(self, **kwargs):
        table_id = kwargs.get('table_id', list(self.tables.keys())[0])
        self.setup_table(self.tables[table_id])
        return self.tables[table_id].refresh_row(self.request, kwargs['row_no'])

    def view_filter(self, query, table):
        if hasattr(table.model, 'query_filter'):
            return table.model.query_filter(query, self.request, table=table)
        return query

    def add_table(self, table_id, **kwargs):
        self.tables[table_id] = DatatableTable(table_id, table_options=self.table_options,
                                               table_classes=self.table_classes, view=self, **kwargs)

    def add_tables(self):
        self.add_table(type(self).__name__.lower(), model=self.model)

    def setup_tables(self, table_id=None):
        for t_id, table in self.tables.items() if not table_id else [(table_id, self.tables[table_id])]:
            getattr(self, 'setup_' + t_id, self.setup_table)(table)
            table.view_filter = self.view_filter

    def dispatch(self, request, *args, **kwargs):
        self.add_tables()
        self.dispatch_context = detect_device(request)
        return super(DatatableView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
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
    def get_table_query(table, **kwargs):
        return table.get_query(**kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('datatable_data'):
            table = self.tables[request.POST['table_id']]
            self.setup_tables(table_id=table.table_id)
            if table.cache_data is True:
                from .cache import DataTableCache
                datatable_cache = DataTableCache()
                cache = datatable_cache.get_cache(table)
                if cache:
                    return HttpResponse(cache, content_type='application/json')
            results = self.get_table_query(table, **kwargs)
            table_data = table.get_json(request, results)
            if table.cache_data is True:
                datatable_cache.store_cache(table, table_data)
            return HttpResponse(table_data, content_type='application/json')
        if hasattr(super(), 'post'):
            # noinspection PyUnresolvedReferences
            return super().post(request, *args, **kwargs)
        elif is_ajax(request) and request.content_type == 'application/json':
            response = json.loads(request.body)
            raise Exception(f'May need to use AjaxHelpers Mixin or'
                            f' add one of these \n{", ".join(response.keys())}\nto ajax_commands ')

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
        self.setup_tables()
        context = super().get_context_data(**kwargs)
        if len(self.tables) == 1:
            context['datatable'] = self.tables[list(self.tables.keys())[0]]
        else:
            context['datatables'] = self.tables
        context.update(self.add_to_context(**kwargs))
        return context

    def add_to_context(self, **kwargs):
        return {}

    def button_datatable_save_state(self, state, table_id, **kwargs):
        saved_state = SavedState.objects.get_or_create(name=kwargs['name'], table_id=table_id)[0]
        saved_state.state = json.dumps(state)
        saved_state.save()
        return self.command_response('delay', time=1)

    def button_datatable_load_state(self, table_id, name, state_id, **kwargs):
        saved_state = SavedState.objects.get(id=int(state_id))
        self.add_command('restore_datatable', state=saved_state.state, table_id=table_id, state_id=saved_state.id)
        return self.command_response('reload')

    def row_column(self, **kwargs):
        self.setup_tables(kwargs['table_id'])
        column = self.tables[kwargs['table_id']].columns[kwargs['column']]
        if hasattr(column, 'row_column'):
            response = getattr(column, 'row_column')(**kwargs)
            if hasattr(response, '__class__') and issubclass(response.__class__, HttpResponseBase):
                return response
            else:
                return self.command_response(response)
