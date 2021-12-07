import re
import copy
import inspect
from types import MethodType
from typing import TypeVar, Dict

from django.forms.widgets import Select

from .helpers import get_url, render_replace, DUMMY_ID

KT = TypeVar('KT')
VT = TypeVar('VT')

EDIT_SEND = 'django_datatables.row_send(this)'
MAKE_EDIT = 'django_datatables.make_edit(this)'
PENCIL = '<i class="cell-edit"></i>'
EDIT_CELL_HTML = f'<div class="cell-div" tabindex="0" onfocus="{MAKE_EDIT}" onclick="$(this).focus()">%1%{PENCIL}</div>'


class ColumnNameError(Exception):
    pass


class DatatableColumnError(Exception):
    pass


class ColumnBase:

    """
    kwargs
        * **enabled** not included in table columns
        * **hidden** not displayed by default may be overridden by table saving options
    """

    popover_html = ('<button type="button" class="ml-1 btn btn-link p-0" data-html=true data-placement="top" '
                    'data-toggle="popover" data-content="{}"><i class="far fa-question-circle"></i></button>')

    @staticmethod
    def merge_kwargs_locals(local_vars):
        kwargs = local_vars.pop('kwargs', {})
        kwargs.update(local_vars)
        del kwargs['self']
        kwargs.pop('__class__', None)
        return kwargs

    def initialise(self, local_vars):
        if not hasattr(self, 'initialised'):
            self.kwargs = self.merge_kwargs_locals(local_vars)
            # noinspection PyAttributeOutsideInit
            self.initialised = 'column_name' in self.kwargs or hasattr(self, 'column_name')
        return self.initialised

    def get_class_instance(self, column_name, **kwargs):
        kwargs.update(self.kwargs)
        return self.__class__(column_name=column_name, class_holder=False, **kwargs)

    def extract_args(self):
        args = self.column_name.split('|')
        return_args = []
        if len(args) > 1:
            self.column_name = args[0]
            for a in args[1:]:
                split_arg = a.split('=')
                if len(split_arg) == 2:
                    self.kwargs[split_arg[0]] = split_arg[1]
                else:
                    return_args.append(a)
        return return_args

    def __init__(self, field=None, **kwargs):
        if not self.initialise(locals()):
            return
        # Remove  ._$ characters from beginning of name and set appropriate options
        self._column_name = None
        self.options: Dict[KT, VT] = {}
        self.column_defs = {}
        self.column_name, options = self.extract_options(kwargs.get('column_name', ''))
        self.options: Dict[KT, VT] = options
        self.model_path = kwargs.pop('model_path', None)
        if not self.model_path is not None:
            self.model_path = self.get_model_path(self.column_name)
            if '/' in self.model_path:
                self.model_path = self.model_path[self.model_path.find('/') + 1:]
        self.model = kwargs.pop('model', None)
        self.table = kwargs.pop('table', None)
        self.enabled = kwargs.pop('enabled', True)
        if kwargs.pop('column_name', None) == field:
            self.field = self.column_name
        else:
            self.field = field
        self.args = self.extract_args()
        self.title = self.title_from_name(self.column_name)
        self.column_type = 0
        self._annotations = None
        self._annotations_value = None
        self._aggregations = None
        self.additional_columns = []
        self.kwargs = kwargs
        self.replace_list = []
        self.blank = None
        self.popover = None
        self.setup_kwargs(kwargs)
        self.result_processes = {}
        self.col_setup()
        self.edit_type = None

        if self.table and self.column_name in getattr(self.table, 'edit_fields', []):
            self.setup_edit()

        if not hasattr(self, 'row_result'):
            self.row_result = MethodType(self.__row_result, self)

    def dropdown_edit(self, choices):
        options = self.table.edit_options.get(self.column_name, {})
        attrs = {} if options.get('select2') else {'onchange': '$(this).blur()', 'onfocusout': f'{EDIT_SEND}'}
        return {'render': [render_replace(column=self.column_name + ':1', html=EDIT_CELL_HTML)],
                'field_array': True,
                'input_html': Select(choices=choices).render('', '', attrs=attrs),
                'edit_options': options}

    def setup_edit(self):
        if '__' in self.field:
            if self.field.count('__') > 1:
                raise DatatableColumnError('Cannot edit this field')
            self.edit_type = 'FK'
            field = self.field[self.field.find('__') + 2:]
            choices = list(self.model.objects.values_list('id', field))
            self.field = ['id', field]
            self.options.update(self.dropdown_edit(choices))
        else:
            self.options['render'] = [render_replace(column=self.column_name, html=EDIT_CELL_HTML)]
            self.options['input_html'] = f'<input class="cell-input" onfocusout="{EDIT_SEND}" type="text">'

    def alter_object(self, row_object, value):
        if self.edit_type == 'FK':
            setattr(row_object, self.field[0][:self.field[0].find('__')] + '_id', value[0])
        else:
            setattr(row_object, self.field, value)
        row_object.save()

    def col_setup(self):
        pass

    @property
    def annotations(self):
        return self._annotations

    @annotations.setter
    def annotations(self, value):
        self._annotations = self._set_annotations(value)

    @property
    def annotations_value(self):
        return self._annotations_value

    @annotations_value.setter
    def annotations_value(self, value):
        self._annotations_value = self._set_annotations(value)

    def _set_annotations(self, value):
        annotations = copy.deepcopy(value)
        if self.model_path:
            new_annotations = {}
            for k in annotations:
                new_annotations[self.model_path + k] = annotations[k]
                for e in new_annotations[self.model_path + k].source_expressions:
                    e.name = self.model_path + e.name
            annotations = new_annotations
        for f in annotations:
            if self.field is None:
                self._field = f
            elif type(self.field) == str:
                if f != self.field:
                    self._field = [self.field, f]
            else:
                if f not in self.field:
                    self._field.append(f)
        return annotations

    def get_annotations(self, **_kwargs):
        return self._annotations

    @property
    def aggregations(self):
        return self._aggregations

    @aggregations.setter
    def aggregations(self, value):
        self._aggregations = self._set_aggregations(value)

    def _set_aggregations(self, value):
        aggregations = copy.deepcopy(value)
        return aggregations

    @property
    def column_name(self):
        return self._column_name

    @column_name.setter
    def column_name(self, value):
        if not re.match('^[A-Za-z0-9._/]+$', value):
            raise ColumnNameError('Invalid column_name: ' + value)
        self._column_name = value

    @property
    def field(self):
        return self._field

    @field.setter
    def field(self, fields):
        if fields is None:
            self._field = None
        elif isinstance(fields, (list, tuple)):
            self.options['field_array'] = True
            self._field = [self.model_path + o for o in fields]
            if not hasattr(self, 'row_result') or type(self.row_result.__self__) == ColumnBase:
                self.row_result = MethodType(self.__list_row_result, self)
        else:
            self._field = self.model_path + fields

    def field_append(self, field):
        if not isinstance(self._field, (list, tuple)):
            self._field = [self._field, self.model_path + field]
        else:
            self._field = list(self._field).append(self.model_path + field)

    @staticmethod
    def get_model_path(field):
        if '__' in field:
            return '__'.join(field.split('__')[:-1]) + '__'
        else:
            return ''

    @staticmethod
    def extract_options(field):
        attributes = re.search('^[._$]+', field)
        options = {}
        if attributes:
            field = field[attributes.end():]
            if '_' in attributes.group():
                options['calculated'] = True
            if '.' in attributes.group():
                options['hidden'] = True
            if '$' in attributes.group():
                options['secure'] = True
        return field, options

    def setup_results(self, request, all_results):
        return

    @staticmethod
    def __list_row_result(self, data_dict, _page_results):
        return [data_dict.get(f) for f in self.field]

    @staticmethod
    def __row_result(self, data_dict, _page_results):
        if self.options.get('choices'):
            return self.options['choices'].get(data_dict.get(self.field))
        if self.blank:
            ret_val = data_dict.get(self.field)
            if not ret_val:
                return self.blank
            return ret_val
        return data_dict.get(self.field)

    def style(self):
        col_def_str = self.column_defs
        if self.options.get('hidden'):
            col_def_str['visible'] = False
            col_def_str['searchable'] = False
        return col_def_str

    def replace_list_append(self, replace, column, in_column=None, values=None):
        replace_options = {'column': column, 'var': replace}
        if in_column:
            replace_options.update({'in': in_column, 'values': values})
        self.replace_list.append(replace_options)

    @staticmethod
    def title_from_name(name):
        if type(name) == str and len(name) > 0:
            field_no_path = name.split('/')[-1].split('__')[-1]
            if field_no_path.find('_') > 0:
                return field_no_path.replace('_', ' ').title()
            else:
                title = field_no_path[0].upper()
                for letter in field_no_path[1:]:
                    if letter.isupper():
                        title += ' '
                    title += letter
                return title

    def setup_kwargs(self, kwargs):

        for a, value in kwargs.items():
            if a in ['field', 'column_name']:
                continue
            if a == 'row_result':
                self.row_result = MethodType(value, self)
            elif a == 'width':
                self.column_defs['width'] = value
            elif hasattr(self, a):
                setattr(self, a, value)
            else:
                self.options[a] = value
        return self


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

    def __init__(self, *, url_name, link_ref_column='id', link_html=None, link_css='', var='%1%', **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        link_ref_column = self.model_path + link_ref_column
        self.url = url_name

        if not link_html:
            link_html = self.base_link_html

        if not link_css:
            link_css = self.base_link_css
        link_css = f' class="{link_css}"' if link_css else ''
        link = f'<a{link_css} href="{self.url}">{{}}</a>'
        if isinstance(self.field, (list, tuple)):
            self.options['render'] = [
                render_replace(column=self.column_name + ':0', html=link.format('%1%'), var='999999'),
                render_replace(column=self.column_name + ':1'),
            ]
        elif var not in link_html:
            self.options['render'] = [render_replace(column=link_ref_column, html=link.format(link_html), var='999999')]
        else:
            self.options['render'] = [render_replace(column=self.column_name, html=link.format(link_html), var=var),
                                      render_replace(column=link_ref_column, var='999999')]


class ManyToManyColumn(DatatableColumn):

    def setup_results(self, request, all_results):
        if self.reverse:
            tags = self.related_model.objects.values_list(self.field_id, 'pk')
        else:
            tags = self.model.objects.values_list('pk', self.field_id)
        tags = tags.filter(**{self.field_id + '__isnull': False})
        if self.kwargs.get('exclude'):
            tags = tags.exclude(**self.kwargs['exclude'])
        if self.kwargs.get('filter'):
            tags = tags.filter(**self.kwargs['filter'])
        tags = tags.distinct()
        tag_dict = {}
        for t in tags:
            tag_dict.setdefault(t[0], []).append(t[1])
        all_results['m2m' + self.column_name] = tag_dict

    def row_result(self, data_dict, page_results):
        return page_results['m2m' + self.column_name].get(data_dict['id'], self.blank)

    def get_lookup(self, fields):
        return list(self.related_model.objects.values_list('pk', fields[-1]))

    def __init__(self, *,  html=' %1% ', **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        fields = self.field.split('__')
        if not inspect.isclass(self.model):
            raise DatatableColumnError('ManyToManyColumn must have model set')
        # noinspection PyProtectedMember
        connecting_field = self.model._meta.get_field(fields[-2])
        self.related_model = connecting_field.related_model
        if hasattr(connecting_field, 'field'):
            self.field_id = connecting_field.field.attname + '__pk'
            self.reverse = True
        else:
            self.field_id = fields[-2] + '__pk'
            self.reverse = False
        self.field = None
        self.options['lookup'] = kwargs.pop('lookup', self.get_lookup(fields=fields))
        if 'blank' in kwargs:
            self.options['lookup'].append((-1, kwargs.pop('blank')))
            self.blank = [-1]
        else:
            self.blank = []
        self.options['render'] = [{'var': '%1%', 'html': html, 'function': 'ReplaceLookup'}]
        self.setup_kwargs(kwargs)


class DateColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            date = data[self.field].strftime('%d/%m/%Y')
            return date
        except AttributeError:
            return ""


class DateTimeColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            date = data[self.field].strftime('%d/%m/%Y')
            time_str = data[self.field].strftime('%H:%M')
            return date + ' ' + time_str
        except AttributeError:
            return ""


class ChoiceColumn(ColumnBase):

    def setup_kwargs(self, kwarg_dict):
        choices = kwarg_dict.pop('choices')
        self.choices = {c[0]: c[1] for c in choices}
        super().setup_kwargs(kwarg_dict)

    def row_result(self, data, _page_data):
        return self.choices.get(data[self.field], '')

    def setup_edit(self):
        choices = list(self.choices.items())
        self.options.update(self.dropdown_edit(choices))
        self.row_result = self.edit_row_result

    def edit_row_result(self, data, _page_data):
        return [data[self.field], self.choices.get(data[self.field], '')]

    def alter_object(self, row_object, value):
        setattr(row_object, self.field, value[0])
        row_object.save()


class CurrencyPenceColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            return '{:.2f}'.format(data[self.field] / 100.0)
        except KeyError:
            return

    def setup_kwargs(self, kwargs):
        super().setup_kwargs(kwargs)
        self.column_defs = {'className': 'dt-right'}


class CurrencyColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            return '{:.2f}'.format(data[self.field])
        except KeyError:
            return

    def setup_kwargs(self, kwargs):
        super().setup_kwargs(kwargs)
        self.column_defs = {'className': 'dt-right'}


class BooleanColumn(DatatableColumn):

    def __init__(self, *,  choices=None, **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**kwargs)
        if choices:
            self.choices = choices
        else:
            self.choices = ['true', 'false', None]

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
        menu_rendered = menu.render().replace(str(DUMMY_ID), '%1%')
        kwargs['render'] = [render_replace(html=menu_rendered, column=kwargs['column_name'])]
        super().__init__(**kwargs)
