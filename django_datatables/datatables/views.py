import json

from ajax_helpers.utils import is_ajax, ajax_command
from django.http import HttpResponse
from django.http.response import HttpResponseBase
from django.views.generic import TemplateView

from django_datatables.datatables import DatatableTable
from django_datatables.detect_device import detect_device
from django_datatables.models import SavedState


class DatatableView(TemplateView):
    model = None
    table_classes = None
    table_options = None
    ajax_commands = ['row']

    command_response : callable
    add_command: callable


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

    @staticmethod
    def max_records_warning(table):
        table.ajax_commands.append(
            ajax_command('html', selector=f'#{table.table_id}-above',
                         html=f'<div class="alert alert-warning"><b>Not all results shown.</b> '
                              f'Limited to {table.max_records}</div>')
        )

    def dispatch(self, request, *args, **kwargs):
        self.add_tables()
        self.dispatch_context = detect_device(request)
        return super(DatatableView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

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
                from django_datatables.cache import DataTableCache
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
