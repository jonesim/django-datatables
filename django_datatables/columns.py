import re
import inspect
from types import MethodType
from typing import TypeVar, Dict
from .helpers import get_url, render_replace
KT = TypeVar('KT')
VT = TypeVar('VT')


class ColumnNameError(Exception):
    pass


class DatatableColumnError(Exception):
    pass


class ColumnBase:

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
        self.model_path = kwargs.get('model_path')
        if not self.model_path:
            self.model_path = self.get_model_path(self.column_name)
        self.model = kwargs.get('model')
        if kwargs.get('column_name') == field:
            self.field = self.column_name
        else:
            self.field = field
        self.args = self.extract_args()
        self.title = self.title_from_name(self.column_name)
        self.column_type = 0
        self._annotations = None
        self.additional_columns = []
        self.kwargs = kwargs
        self.replace_list = []
        if not hasattr(self, 'row_result'):
            self.row_result = MethodType(self.__row_result, self)
        self.setup_kwargs(kwargs)

    @property
    def annotations(self):
        return self._annotations

    @annotations.setter
    def annotations(self, value):
        for f in value:
            if self.field is None:
                self._field = f
            elif type(self.field) == str:
                if f != self.field:
                    self._field = [self.field, f]
            else:
                if f not in self.field:
                    self._field.append(f)
        self._annotations = value

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
    def __row_result(self, data_dict, _page_results):
        if isinstance(self.field, (list, tuple)):
            return [data_dict.get(f) for f in self.field]
        if self.options.get('choices'):
            return self.options['choices'].get(data_dict.get(self.field))
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
            field_no_path = name.split('__')[-1]
            if field_no_path.find('_') > 0:
                return field_no_path.replace('_', ' ').title()
            else:
                title = field_no_path[0]
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
        self.col_setup()

    def col_setup(self):
        pass


class LambdaColumn(ColumnBase):

    def __init__(self, *, lambda_function, **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**kwargs)
        self.lambda_function = lambda_function

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

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url_name):
        self._url = get_url(url_name)

    def __init__(self, *, url_name, link_ref_column='id', link_html='%1%', var='%1%', **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        self.url = url_name
        if var not in link_html:
            self.options['render'] = [render_replace(column=link_ref_column,
                                                     html=f'<a href="{self.url}">{link_html}</a>',
                                                     var='999999')]
        else:
            self.options['render'] = [render_replace(column=self.column_name,
                                                     html=f'<a href="{self.url}">{link_html}</a>',
                                                     var=var), render_replace(column=link_ref_column, var='999999')]


class ManyToManyColumn(DatatableColumn):

    def setup_results(self, request, all_results):
        if self.reverse:
            tags = self.related_model.objects.values_list(self.field_id, 'id')
        else:
            tags = self.model.objects.values_list('id', self.field_id)
        tags = tags.filter(**{self.field_id + '__isnull': False}).distinct()
        tag_dict = {}
        for t in tags:
            tag_dict.setdefault(t[0], []).append(t[1])
        all_results['m2m' + self.column_name] = tag_dict

    def row_result(self, data_dict, page_results):
        return page_results['m2m' + self.column_name].get(data_dict['id'], [])

    def __init__(self, *,  html=' %1% ', **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        fields = self.field.split('__')
        if not inspect.isclass(self.model):
            raise DatatableColumnError('ManyToManyColumn must have model set')
        connecting_field = self.model._meta.get_field(fields[-2])
        self.related_model = connecting_field.related_model
        if hasattr(connecting_field, 'field'):
            self.field_id = connecting_field.field.attname + '__id'
            self.reverse = True
        else:
            self.field_id = fields[-2] + '__id'
            self.reverse = False
        self.field = None
        self.options['lookup'] = list(self.related_model.objects.values_list('id', fields[-1]))
        self.options['render'] = [{'var': '%1%', 'html': html, 'function': 'ReplaceLookup'}]


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
        self.options = {c[0]: c[1] for c in choices}
        super().setup_kwargs(kwarg_dict)

    def row_result(self, data, _page_data):
        return self.options.get(data[self.field], '')


class CurrencyPenceColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            return '{:.2f}'.format(data[self.field] / 100.0)
        except KeyError:
            return


class CurrencyColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            return '{:.2f}'.format(data[self.field])
        except KeyError:
            return


class BooleanColumn(ColumnBase):

    def row_result(self, data, _page_data):
        try:
            if data[self.field]:
                return 'true'
            else:
                return 'false'
        except KeyError:
            return
