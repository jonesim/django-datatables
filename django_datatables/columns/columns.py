from django_datatables.columns.column_base import ColumnBase
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

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url_name):
        self._url = get_url(url_name)

    def __init__(self, *, url_name, link_ref_column=None, link_html=None, link_css='', var='%1%', **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        if link_ref_column:
            link_ref_column = self.model_path + link_ref_column
        else:
            link_ref_column = self.column_name
        self.url = url_name

        if not link_html:
            link_html = self.base_link_html

        if not link_css:
            link_css = self.base_link_css

        self.var = var
        self.link_ref_column = link_ref_column
        self.setup_link(link_css, link_html)

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

    def setup_link(self, link_css, link_html):
        link_css = f' class="{link_css}"' if link_css else ''
        link = f'<a{link_css} href="{self.url}">{{}}</a>'
        if isinstance(self.field, (list, tuple)):
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

    def __init__(self, *,  choices=None, replace=None, **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**kwargs)
        if choices:
            self.choices = choices
        else:
            self.choices = ['true', 'false', None]

        if replace:
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
        kwargs['title'] = '<div class="d-flex" style="width:40px;line-height:14px"><div class="m-auto">{}{}</div></div>'.format(
            button('Select all', 'fas fa-check-square'), button('Unselect all', 'far fa-square', 'clear')
        )
        kwargs['render'] = [{'function': 'Replace',
                             'html': ('<input class="col-sel" type="checkbox"%2% name="%1%" title="Select" '
                                      'onchange="django_datatables.select_item(this)">'),
                             'var': '%1%'} ,
                            {'function': 'SelectedReplace', 'var': '%2%', 'selected': ' checked'}]
        kwargs['no_col_search'] = True
        kwargs['column_defs'] = {'orderable': False, 'className': 'dt-center'}
        super().__init__(field=field, **kwargs)
