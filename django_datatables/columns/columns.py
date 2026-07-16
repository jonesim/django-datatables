import base64
from html.parser import HTMLParser

from django_menus.menu import HtmlMenu, MenuItem

from django_datatables.columns.column_base import ColumnBase, DatatableColumnError
from django_datatables.columns.currency import CurrencyPenceColumn
from django_datatables.helpers import get_url, render_replace, DUMMY_ID, DUMMY_ID2


class DatatableColumn(ColumnBase):
    def __init__(self, **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**kwargs)


class LambdaColumn(ColumnBase):

    def __init__(self, *, lambda_function, **kwargs):
        if not self.initialise(locals()):
            return
        self.lambda_function = kwargs.pop('lambda_function')
        super().__init__(**kwargs)

    def row_result(self, data_dict, _page_results):
        return self.lambda_function(data_dict.get(self.field))


class TextFieldColumn(ColumnBase):

    def row_result(self, data_dict, _page_results):
        result = data_dict.get(self.field, '')
        if result is None:
            return ''
        if len(result) > self.kwargs.get('max_chars'):
            result = result[:self.kwargs.get('max_chars')] + '...'
        return result.replace('\n', '<br>')

    def __init__(self, max_chars=8000, **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        if len(self.args) > 0:
            self.kwargs['max_chars'] = int(self.args[0])


class ColumnLink(ColumnBase):

    base_link_html = '%1%'
    base_link_css = None
    # Cell alignment: an ``align`` kwarg wins, else this class default. None leaves it unset.
    default_align = None

    def col_setup(self):
        align = self.kwargs.get('align', self.default_align)
        if align:
            self.column_defs['className'] = 'dt-' + align

    @property
    def url(self):
        # When qs_url is set, append the current page path (base64 encoded) as a query
        # string so the linked view can offer a "back" link. Requires the table's view.
        if self.qs_url and self.table and getattr(self.table, 'view', None):
            return (f'{self._url}?{self.qs_url}'
                    f'={base64.urlsafe_b64encode(self.table.view.request.path.encode("utf8")).decode("ascii")}')
        return self._url

    @url.setter
    def url(self, url_name):
        self._url = get_url(url_name)

    def __init__(self, *, url_name=None, link_ref_column=None, link_html=None, link_css='', var='%1%', new_tab=False,
                 qs_url='', **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        if link_ref_column:
            link_ref_column = self.model_path + link_ref_column
        else:
            link_ref_column = self.column_name
        self.qs_url = qs_url
        self.url = url_name if url_name else self.model.url_name

        if not link_html:
            link_html = self.base_link_html

        if not link_css:
            link_css = self.base_link_css

        self.new_tab = new_tab
        self.var = var
        self.link_ref_column = link_ref_column
        self.setup_link(link_css, link_html, new_tab=new_tab)

    def html_result(self, data_dict, page_results):
        from django.utils.html import conditional_escape, escape
        from django.utils.safestring import mark_safe
        from django_datatables.helpers import DUMMY_ID
        value = self.row_result(data_dict, page_results)
        text = value[0] if isinstance(value, list) else value
        ref_value = data_dict.get(self.link_ref_column)
        if ref_value is None:
            return conditional_escape(str(text)) if text is not None else ''
        url = self._url.replace(str(DUMMY_ID), str(ref_value))
        css = f' class="{self.base_link_css}"' if self.base_link_css else ''
        return mark_safe(f'<a{css} href="{escape(url)}">{escape(str(text))}</a>')

    def setup_link(self, link_css, link_html, new_tab=False):
        link_css = f' class="{link_css}"' if link_css else ''
        target = 'target="_blank" ' if new_tab else ''
        link = f'<a{link_css} {target}href="{self.url}">{{}}</a>'
        if isinstance(self.field, (list, tuple)):
            # field[0] is the URL reference, field[1] the displayed text. Default the
            # server-side search/sort target to the displayed field (already prefixed)
            # unless the developer set search_field explicitly (or opted out with False).
            if self._search_field is None and len(self.field) > 1:
                self._search_field = [self.field[1]]
            self.options['render'] = [
                render_replace(column=self.column_name + ':0', html=link.format(link_html), var='999999'),
                render_replace(column=self.column_name + ':1'),
            ]
        elif self.var not in link_html:
            self.options['render'] = [render_replace(column=self.link_ref_column,
                                                     html=link.format(link_html), var='999999')]
        else:
            self.options['render'] = [render_replace(column=self.column_name,
                                                     html=link.format(link_html),
                                                     var=self.var),
                                      render_replace(column=self.link_ref_column, var='999999')]



class ChoiceColumn(ColumnBase):

    def setup_kwargs(self, kwarg_dict):
        choices = kwarg_dict.pop('choices')
        self.choices = {c[0]: c[1] for c in choices}
        super().setup_kwargs(kwarg_dict)

    def row_result(self, data, _page_data):
        return self.choices.get(data.get(self.field), '')

    def setup_edit(self):
        choices = list(self.choices.items())
        self.options.update(self.dropdown_edit(choices))
        self.row_result = self.edit_row_result

    def edit_row_result(self, data, _page_data):
        return [data[self.field], self.choices.get(data[self.field], '')]

    def alter_object(self, row_object, value):
        setattr(row_object, self.field, value[0])
        row_object.save()



class BooleanColumn(DatatableColumn):
    """Render a boolean field as ``choices`` = [true_value, false_value, none_value].

    Passing ``replace`` (or setting ``default_replace``) renders each choice as the
    corresponding html instead - see ``TickColumn`` for a preset.
    """

    default_choices = ['true', 'false', None]
    default_replace = None

    def __init__(self, *,  choices=None, replace=None, **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**kwargs)
        self.choices = choices if choices else list(self.default_choices)
        replace = replace if replace else self.default_replace
        if replace:
            self.setup_replace(replace)

    def setup_replace(self, replace):
        self.options['render'] = [{'function': 'ReplaceLookup', 'html': '%1%', 'var': '%1%'}]
        self.options['lookup'] = [(self.choices[c], r) for c, r in enumerate(replace)]
        self.options['no_col_search'] = True

    def row_result(self, data, _page_data):
        try:
            if data[self.field] is None:
                return self.choices[-1]
            return self.choices[0] if data[self.field] else self.choices[1]
        except KeyError:
            return


class GroupedColumn(DatatableColumn):

    page_key = ''

    @staticmethod
    def initial_column_data(_request):
        return ''

    def setup_results(self, request, all_results):
        all_results[self.page_key] = self.initial_column_data(request)

    def row_result(self, data, page_data):
        return page_data[self.page_key].get(data[self.field])


class CallableColumn(DatatableColumn):

    def row_result(self, data_dict, _page_results):
        fake_object = type('fake', (), {k[len(self.model_path):]: v
                                        for k, v in data_dict.items()
                                        if k.startswith(self.model_path)})
        return self.object_function(fake_object)

    def setup_kwargs(self, kwargs):
        super().setup_kwargs(kwargs)
        self.object_function = getattr(self.model, self.field[len(self.model_path):])
        self.field = kwargs.get('parameters')


class NoHeadingColumn(DatatableColumn):
    def __init__(self, **kwargs):
        kwargs['title'] = ''
        kwargs['no_col_search'] = True
        kwargs['column_defs'] = {'orderable': False}
        super().__init__(**kwargs)


class MenuColumn(NoHeadingColumn):
    """
    This is used to render a django-menus in a column.
    example:

    MenuColumn(column_name='menu', field='id', menu=HtmlMenu(self.request, 'button_group').add_items(
                    ('view 1', 'View 1', {'url_kwargs': {'int': DUMMY_ID}}),
                    ('view 2', 'View 2', {'url_kwargs': {'int': DUMMY_ID}})
                )),
    """
    def __init__(self, menu, **kwargs):
        column_name = kwargs['column_name']
        menu_rendered = menu.render().replace(str(DUMMY_ID), '%1%').replace(str(DUMMY_ID2), '%2%')
        if isinstance(kwargs['field'], (list, tuple)):
            kwargs['render'] = [
                    render_replace(column=column_name + ':0', html=menu_rendered, var='%1%'),
                    render_replace(column=column_name + ':1', var='%2%'),
                ]
        else:
            kwargs['render'] = [render_replace(html=menu_rendered, column=column_name)]
        super().__init__(**kwargs)


class SelectColumn(DatatableColumn):

    def __init__(self, field='id', **kwargs):
        def button(title, font_awesome, data_command=None):
            return (
                f'''<button class="table-select" onclick="django_datatables.column_select(this)" title="{title}"'''
                f'''{(f' data-command="' + data_command + '"') if data_command else ''}>'''
                f'''<i class="{font_awesome}"></i></button>'''
            )
        kwargs.setdefault(
            'title',
            '<div class="d-flex" style="width:40px;line-height:14px"><div class="m-auto">{}{}</div></div>'.format(
                button('Select all', 'fas fa-check-square'), button('Unselect all', 'far fa-square', 'clear')
            )
        )
        kwargs['render'] = [{'function': 'Replace',
                             'html': ('<input class="col-sel" type="checkbox"%2% name="%1%" title="Select" '
                                      'onchange="django_datatables.select_item(this)">'),
                             'var': '%1%'} ,
                            {'function': 'SelectedReplace', 'var': '%2%', 'selected': ' checked'}]
        kwargs['no_col_search'] = True
        kwargs['column_defs'] = {'orderable': False, 'className': 'dt-center'}
        super().__init__(field=field, **kwargs)


class SelectColumnNoTitle(SelectColumn):
    """SelectColumn without the select all / unselect all header.

    Equivalent to ``SelectColumn(title='')``, which is the preferred spelling.
    """

    def col_setup(self):
        self.title = ''


class ZeroPenceColumn(CurrencyPenceColumn):
    """Like CurrencyPenceColumn but renders zero instead of a blank cell for a null / missing value."""

    def row_result(self, data_dict, page_results):
        result = super().row_result(data_dict, page_results)
        return result if result is not None else '{:.2f}'.format(0)


class MonthColumn(DatatableColumn):
    """Render a date field as 'YYYY MM'."""

    def row_result(self, data, _page_data):
        try:
            return data[self.field].strftime('%Y %m')
        except AttributeError:
            return ""


class YearMonthColumn(MonthColumn):
    """Hidden MonthColumn (e.g. for grouping / sorting).

    Equivalent to a MonthColumn with a '.'-prefixed column_name, which is the preferred spelling.
    """

    def col_setup(self):
        self.options['hidden'] = True


TICK_REPLACE = ('<i class="text-success fas fa-check-circle">&nbsp;</i>', ' ')


class TickColumn(BooleanColumn):
    """BooleanColumn preset: a green tick for true, blank for false."""

    default_replace = TICK_REPLACE


class TableRowColour(DatatableColumn):
    """Hidden column whose value can drive per-row colouring.

    Equivalent to a DatatableColumn with a '.'-prefixed column_name, which is the preferred spelling.
    """

    def col_setup(self):
        self.options['hidden'] = True


class AlignColumnLink(ColumnLink):
    """ColumnLink defaulting to a centred cell.

    Equivalent to ``ColumnLink(align='center')``, which is the preferred spelling.
    """

    default_align = 'center'


class XlColumnLink(ColumnLink):
    """ColumnLink whose Excel export uses the display text (second element) of a [ref, text] value."""

    @staticmethod
    def excel(value):
        if isinstance(value, list):
            return value[1]


class ViewLink(ColumnLink):
    """ColumnLink preset rendering a small 'View' button (right aligned)."""

    default_align = 'right'

    def __init__(self, **kwargs):
        default_kwargs = {'field': 'id', 'link_html': '<button class="btn btn-sm btn-outline-dark">View</button>'}
        default_kwargs.update(kwargs)
        super().__init__(**default_kwargs)


class JsonBooleanColumn(BooleanColumn):
    """Display a boolean key from a JSON field, rendered as a tick / blank (or custom choices)."""

    default_choices = ['Yes', 'No']
    default_replace = TICK_REPLACE

    def __init__(self, *, json_key=None, field=None, **kwargs):
        if not self.initialise(locals()):
            return
        # initialise() has already merged field / json_key into kwargs, so override in place.
        kwargs['field'] = field if field else 'options'
        super().__init__(**kwargs)
        self.json_key = json_key

    def col_setup(self):
        self.column_defs['width'] = '60px'

    def row_result(self, data_dict, _page_results):
        # The JSON field itself may be null, not just the key.
        return self.choices[0] if (data_dict[self.field] or {}).get(self.json_key) else self.choices[1]


class JsonKeyColumn(DatatableColumn):
    """Display an arbitrary key from a JSON field (pass json_key=...)."""

    def row_result(self, data_dict, _page_results):
        return data_dict[self.field].get(self.kwargs['json_key'])


class MultiMenuColumnBase(NoHeadingColumn):
    """Base for a column that renders one of several per-row django-menus, chosen by row id.

    Subclasses build their menus (via ``add_menu``) inside ``col_setup``; that needs the table /
    view to be attached, so ``add_menu`` raises a clear error if used before the view is available.
    """
    css = {'css_classes': 'btn btn-sm btn-outline-dark'}
    default_kwargs = dict(url_kwargs={'slug': DUMMY_ID}, css_classes='btn btn-sm btn-outline-dark', menu_display='')

    def __init__(self, **kwargs):
        self.menus = []
        super().__init__(**kwargs)

    @property
    def request(self):
        view = getattr(self.table, 'view', None) if self.table else None
        if view is None:
            raise DatatableColumnError('MultiMenuColumnBase needs its table/view attached before building menus')
        return view.request

    def add_menu(self, menu_id, *items):
        self.menus.append([menu_id, HtmlMenu(self.request, 'button_group').add_items(*items).render()])

    @staticmethod
    def some_menu(url, tooltip=None):
        return MenuItem(url=url, font_awesome='fa fa-check-double', **({'tooltip': tooltip} if tooltip else {}),
                        url_kwargs={'slug': DUMMY_ID}, css_classes='btn btn-sm btn-outline-dark', menu_display='')

    def col_setup(self):
        self.options['render'] = [{'function': 'ReplaceLookup', 'html': '%1%', 'var': '%1%'},
                                  {'function': 'Replace', 'var': DUMMY_ID, 'column': 'id'}]
        self.options['lookup'] = self.menus
        self.column_defs['width'] = '120px'


class _HtmlTextFilter(HTMLParser):
    """Collect the text nodes of an HTML fragment, joined by a delimiter."""

    def __init__(self, delimiter=''):
        self.delimiter = delimiter
        self.text = ''
        super().__init__()

    def handle_data(self, data):
        if data:
            self.text += self.delimiter + data if self.text else data


class ExcelDatatableColumn(DatatableColumn):
    """DatatableColumn whose Excel export is the plain text of its (HTML) cell value."""

    @staticmethod
    def excel(value):
        if value is None:
            return ''
        f = _HtmlTextFilter(', ')
        f.feed(str(value))
        return f.text
