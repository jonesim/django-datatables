import base64
import json
from collections.abc import Callable

from ajax_helpers.mixins import ajax_method
from django.http import HttpRequest
from django_modals.helper import ajax_modal_replace

from django_datatables.column_visibility.modals import ColumnForm, DatatableColumnModal, save_table_state
from django_datatables.models import SavedState


class ColumnVisibilityMixin:

    setup_tables: Callable
    tables: dict
    command_response: Callable
    request: HttpRequest
    all_columns : bool
    ajax_commands = ['datatable']

    def session_states(self, table_id, name='_default'):
        return SavedState.objects.filter(user_id=self.request.user.id, name=name,
                                         table_id=table_id, view_class=self.__class__.__name__)

    def column_form(self, datatable_id):
        self.all_columns = True
        self.setup_tables(table_id=datatable_id)
        return ColumnForm.create_from_table(self.tables[datatable_id],
                                            has_default=len(self.session_states(datatable_id)) > 0)

    @ajax_method
    def datatable_columns(self, datatable):
        return self.command_response(ajax_modal_replace(self.request, modal_class=DatatableColumnModal,
                                                        ajax_function='modal_html',
                                                        form_class=self.column_form(datatable)))

    def post(self, request, **kwargs):
        if 'modal_id' in request.POST and 'ajax_method' not in request.POST:
            if request.POST.get('modal') == 'clear_session':
                self.session_states(table_id=request.POST['table_id']).delete()
                return self.command_response('reload')
            elif request.POST.get('modal') == 'set_columns':
                return DatatableColumnModal.as_view()(
                    request, form_class=self.column_form(request.POST['datatable']),
                    url_name=request.resolver_match.url_name, url_kwargs=request.resolver_match.kwargs, **kwargs
                )
        # noinspection PyUnresolvedReferences
        return super().post(request, **kwargs)

    def column_column_order(self, column_data, table_id, name, **_kwargs):
        # This starts a chain saving order then state from browser local storage and finally visibility

        column_data = json.loads(column_data)
        padding = '=' * (-len(table_id) % 4)
        view_class, table_id = base64.b64decode(table_id + padding).decode("utf-8").split('.')
        if self.request.session.session_key is None:
            self.request.session.save()
        if name == '_default':
            self.session_states(table_id=table_id, name='_session').delete()
        save_table_state(user_id=self.request.user.id, table_id=table_id, name=name,
                         column_order={column_name: c for c, column_name in enumerate(column_data)},
                         view_class=view_class)
        return self.command_response('get_datatable_state', table_id=table_id,
                                     data={'ajax_method': 'state_response', 'view_class': view_class,
                                           'table_id': table_id, 'name': name})

    @ajax_method
    def state_response(self, view_class, table_id, val, name, **_kwargs):
        val = json.loads(val)
        if name=='_default':
            del val['session_id']
        else:
            val['session_id'] = self.request.session.session_key
        val = json.dumps(val)
        save_table_state(self.request.user.id, table_id, view_class, state=val, name=name)
        return self.command_response('post_modal', button = {'datatable': table_id, 'view_class': view_class,
                                                             'modal': 'set_columns', 'name': name})
