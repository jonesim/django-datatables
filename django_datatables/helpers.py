from ajax_helpers.utils import ajax_command
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
    if type(url_name) == tuple:
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


def send_selected(table_id, method_name):
    return (f"ajax_helpers.process_commands([{{function:'send_selected', "
            f"table_id:'{table_id}', method: '{method_name}'}}])")
