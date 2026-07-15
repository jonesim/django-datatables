import importlib

from ajax_helpers.utils import ajax_command
from django.apps import apps
from django.db.models import Q
from django.urls import reverse
DUMMY_ID = 999999
DUMMY_ID2 = 888888

simple_table = {
    'dom': 't',
    'no_col_search': True,
    'no_footer': True,
    'pageLength': 400,
    'stateSave': False
}

note_table_options = {
    'dom': 'trip',
    'no_col_search': True,
    'no_footer': True,
    'pageLength': 50,
    'stateSave': False
}


def extract_fields(row_result):
    """Decorator for a column's row_result that passes the list of this column's field values.

    Wraps ``row_result(self, data_dict, page_results, fields)`` where ``fields`` is the value of
    each entry in ``self.field`` looked up in ``data_dict``.
    """
    def get_fields(self, data_dict, page_results):
        fields = [data_dict.get(f) for f in self.field]
        return row_result(self, data_dict, page_results, fields)
    return get_fields


def add_module_columns(model, module_str, class_name):
    """Copy the public column attributes of ``module_str.class_name`` onto ``model.Datatable``."""
    module = importlib.import_module(module_str)
    column_class = getattr(module, class_name)
    for c in dir(column_class):
        if not c.startswith('_') and not hasattr(model.Datatable, c):
            setattr(model.Datatable, c, getattr(column_class, c))


def add_columns(app_name):
    """Attach columns declared via each model's ``add_columns`` attribute for a whole app."""
    for a in apps.get_models():
        if a._meta.app_label == app_name:
            if hasattr(a, 'add_columns'):
                columns = getattr(a, 'add_columns')
                if isinstance(columns, str):
                    columns = [columns]
                for c in columns:
                    split_c = c.split('.')
                    add_module_columns(a, '.'.join(split_c[:-1]), split_c[-1])


def row_button(command, button_text, *, function='Html', button_classes='btn btn-sm', tooltip=False, title=None,
               **kwargs):
    title = f' title="{title}"' if title else ''
    tooltip = ' data-toggle="tooltip"' if tooltip else ''
    rb = {
        'html': (f'<button{title} data-command="{command}" onclick="django_datatables.b_r(this)" '
                 f'class="{button_classes}"{tooltip}>{button_text}</button>'),
        'function': function,
    }
    rb.update(kwargs)
    return rb


def render_replace(*, var='%1%', row=False, **kwargs):
    if row:
        return dict(var=var, function='Base64Row', **kwargs)
    return dict(var=var, function='Replace', **kwargs)


def get_url(url_name):
    if isinstance(url_name, tuple):
        return reverse(url_name[0], args=[*url_name[1:]])
    else:
        if url_name.find(str(DUMMY_ID)) == -1:
            return reverse(url_name, args=[DUMMY_ID])
        return url_name


def row_link(url_name, column_id):
    return [render_replace(column=column_id, html=get_url(url_name), var=str(DUMMY_ID))]


def overwrite_cell(table, row_no, column_name, html):
    return ajax_command('html',
                        selector=f'#{table.table_id} #{row_no} td:nth-of-type({table.find_column(column_name)[1] + 1})',
                        html=html)


def send_selected(table_id, method_name, modal=False):
    function = 'send_selected_modal' if modal else 'send_selected'
    return (f"ajax_helpers.process_commands([{{function:'{function}', "
            f"table_id:'{table_id}', method: '{method_name}'}}])")


def send_selected_modal(table_id, method_name):
    return send_selected(table_id, method_name, modal=True)


def convert_to_q(filter_dict):
    if isinstance(filter_dict, Q):
        return filter_dict
    q_obj = Q()
    if filter_dict:
        for k, v in filter_dict.items():
            q_obj.children.append((k, v))
    return q_obj


def add_filters(filter1, filter2):
    if not filter2:
        return filter1
    if isinstance(filter1, dict) and isinstance(filter2, dict):
        return {**filter1, **filter2}
    if not isinstance(filter1, Q):
        filter1 = convert_to_q(filter1)
    if not isinstance(filter2, Q):
        filter2 = convert_to_q(filter2)
    return Q(filter1 & filter2)
