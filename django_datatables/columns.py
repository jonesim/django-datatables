import re
import copy
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
        self.model_path = kwargs.pop('model_path', None)
        if not self.model_path:
            self.model_path = self.get_model_path(self.column_name)
            if '/' in self.model_path:
                self.model_path = self.model_path[self.model_path.find('/') + 1:]
        self.model = kwargs.pop('model', None)
        if kwargs.pop('column_name', None) == field:
            self.field = self.column_name
        else:
            self.field = field
        self.args = self.extract_args()
        self.title = self.title_from_name(self.column_name)
        self.column_type = 0
        self._annotations = None
        self._annotations_value = None
        self.additional_columns = []
        self.kwargs = kwargs
        self.replace_list = []
        self.blank = None
        if not hasattr(self, 'row_result'):
            self.row_result = MethodType(self.__row_result, self)
        self.setup_kwargs(kwargs)
        self.col_setup()

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

        if isinstance(self.field, (list, tuple)):
            self.options['render'] = [render_replace(column=self.column_name + ':0',
                                                     html=f'<a href="{self.url}">%1%</a>',
                                                     var='999999'),
                                      render_replace(column=self.column_name + ':1'),
                                      ]
        elif var not in link_html:
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
