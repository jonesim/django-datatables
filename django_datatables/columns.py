import re
from types import MethodType
from django.urls import reverse
# from bootstrap_modals.helper import show_modal
from typing import TypeVar, Dict

KT = TypeVar('KT')
VT = TypeVar('VT')


class ColumnNameError(Exception):
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
            self.initialised = 'column_name' in self.kwargs
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
        self.column_name, options = self.extract_options(kwargs.get('column_name', ''))
        self.options: Dict[KT, VT] = options
        self.args = self.extract_args()
        self.model_path = self.get_model_path(self.column_name)
        self.column_ref = self.column_name
        self.field = field
        self.title = self.title_from_name(self.column_name)
        self.column_type = 0
        self._annotations = None
        self.additional_columns = []
        self.kwargs = kwargs
        self.replace_list = []
        self.row_result = MethodType(self.__row_result, self)
        self.setup_kwargs(kwargs)

    @property
    def annotations(self):
        return self._annotations

    @annotations.setter
    def annotations(self, value):
        if self.field is None:
            self._field = value
        elif type(self.field) == str:
            if value != self.field:
                self._field = [self.field, value]
        else:
            if value not in self.field:
                self._field.append(value)
        self._annotations = value

    @property
    def column_name(self):
        return self._column_name

    @column_name.setter
    def column_name(self, value):
        if not re.match('^[A-Za-z0-9\._]+$', value):
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
    def __row_result(self, data_dict, page_results):
        return data_dict.get(self.field)

    def style(self):
        col_def_str = self.options.get('columnDefs', {})
#        if self.column_type == ColumnDef.COL_CURRENCY or self.column_type == ColumnDef.COL_CURRENCY_PENCE:
#            colDefStr['className'] = 'dt-body-right pr-4'
        if 'mobile' in self.options and not (self.options['mobile']):
            col_def_str['mobile'] = False
        if self.options.get('hidden'):
            col_def_str['visible'] = False
            col_def_str['searchable'] = False
        if 'type' in self.options:
            col_def_str['type'] = self.options['type']
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
            if a == 'row_result':
                self.row_result = MethodType(value, self)
            elif hasattr(self, a):
                setattr(self, a, value)
            else:
                self.options[a] = value
        return self


class DatatableColumn(ColumnBase):
    def __init__(self, **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__( **kwargs)
        self.col_setup()

    def col_setup(self):
        pass


class LambdaColumn(ColumnBase):

    def __init__(self, *, lambda_function, **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**kwargs)
        self.lambda_function = lambda_function

    def row_result(self, data_dict, page_results):
        return self.lambda_function(data_dict.get(self.field))


class TextFieldColumn(ColumnBase):

    def row_result(self, data_dict, page_results):
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


class ColumnReplace(ColumnBase):

    def add_column_reference(self, field, replace_str=None):
        if not replace_str:
            replace_str = f'%r{len(self.replace_list)}%'
        self.replace_list_append(replace_str, field)
        self.additional_columns = [{'field': self.model_path + field,
                                    'column_name': field,
                                    'hidden': True}]
        return replace_str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.options['renderfn'] = 'universalRender'
        self.options['replace_list'] = self.replace_list


class ColumnLink(ColumnReplace):

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url_name):
        if type(url_name) == tuple:
            self._url = reverse(url_name[0], args=[*url_name[1:]])
        else:
            if url_name.find('999999') == -1:
                self._url = reverse(url_name, args=[999999])
            else:
                self._url = url_name

    def __init__(self, *, url_name, link_ref_column='id', link_html='%1%', **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        self.url = url_name
        self.replace_list_append('%1%', self.column_name)
        self.add_column_reference(link_ref_column, replace_str='999999')
        self.options['html'] = f'<a href="{self.url}">{link_html}</a>'


'''
class ModalButton(ColumnReplace):

    def __init__(self, *, modal_name,
                 link_ref_column='id',
                 button_text='Edit',
                 row_modify=False,
                 modal_args=(),
                 **kwargs):
        field = link_ref_column
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        self.replace_list_append('%ref%', kwargs.get('column_name'))
        self.options['no-col-search'] = True
        self.post_init()

    def post_init(self):
        modal_kwargs = {}
        if self.kwargs.get('row_modify'):
            modal_kwargs['row'] = True
        modal_call = show_modal(self.kwargs['modal_name'], "datatable2", *self.kwargs['modal_args'], **modal_kwargs)
        self.options['html'] = f'<a href="javascript:{modal_call}">{self.kwargs["button_text"]}</a>'


class ModalButtonColumn(ColumnReplace):

    def __init__(self, *, modal_name,
                 text_column,
                 link_column='id',
                 row_modify=False,
                 modal_args=(),
                 **kwargs):
        field = text_column
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        self.add_column_reference(link_column, '%ref%')
        self.replace_list_append('%1%', kwargs.get('column_name'))
        modal_kwargs = {}
        if row_modify:
            modal_kwargs['row'] = True
 #       modal_call = show_modal(modal_name, "datatable2", *modal_args, **modal_kwargs)
        self.options['html'] = f'<a href="javascript:{modal_call}">%1%</a>'
        self.post_init()

    def post_init(self):
        pass
'''

def format_date_time(self, data, page_data):
    try:
        date = data[self.field].strftime('%d/%m/%Y')
        time_str = data[self.field].strftime('%H:%M')
        return date
    except AttributeError:
        return ""
