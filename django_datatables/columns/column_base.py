import copy
import json
import re
from types import MethodType
from typing import TypeVar, Dict

from django.db.models.expressions import CombinedExpression
from django.forms.widgets import Select

from django_datatables.helpers import render_replace

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
        if self.model_path is None:
            self.model_path = self.get_model_path(self.column_name)
            if '/' in self.model_path:
                self.model_path = self.model_path[self.model_path.find('/') + 1:]
        self.model = kwargs.pop('model', None)
        self.table = kwargs.pop('table', None)
        self.enabled = kwargs.pop('enabled', True)
        self.hide_options = kwargs.pop('hide_options', None)

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
        self.spreadsheet = kwargs.pop('spreadsheet', {})
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

    def _combined_expression_annotations(self, expression):
        if isinstance(expression.lhs, CombinedExpression):
            self._combined_expression_annotations(expression.lhs)
        else:
            expression.lhs.name = self.model_path + expression.lhs.name
        if isinstance(expression.rhs, CombinedExpression):
            self._combined_expression_annotations(expression.rhs)
        else:
            expression.rhs.name = self.model_path + expression.rhs.name

    def _set_annotations(self, value):
        annotations = copy.deepcopy(value)
        if self.model_path:
            new_annotations = {}
            for k in annotations:
                new_annotations[self.model_path + k] = annotations[k]
                for e in new_annotations[self.model_path + k].source_expressions:
                    if isinstance(e, CombinedExpression):
                        self._combined_expression_annotations(e)
                    else:
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

    @staticmethod
    def excel(value):
        if isinstance(value, (int, float, str)):
            return value
        elif value is None:
            return ''
        return str(value)

    def spreadsheet_init(self):
        column_init = {'title': self.title, 'width': self.column_defs.get('width', 100)}
        column_init.update(self.spreadsheet)

        def allow_javascript(key_pair):
            return key_pair.replace('"', '') if key_pair.startswith(' "editor":') else key_pair

        return '{' + ','.join([(allow_javascript(v))
                               for v in json.dumps(column_init).strip('{').strip('}').split(',')]) + '}'
