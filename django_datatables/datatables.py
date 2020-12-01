import json
from types import MethodType
from inspect import isclass
from typing import TypeVar, Dict
from abc import abstractmethod
from django.db import models
from django.views.generic import TemplateView
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from .detect_device import detect_device
from .columns import ColumnBase, format_date_time
from .model_def import DatatableModel
from .filters import DatatableFilter

KT = TypeVar('KT')
VT = TypeVar('VT')


def options_to_dict(options):
    return dict((x, y) for x, y in options)


DUMMY_ID = 999999

'''
class ColumnDef:
    COL_DEFAULT = -1
    COL_TEXT = 0
    COL_DATE_OF_DATETIME = 1
    COL_DICT_LOOKUP = 3
    COL_BUTTON = 4
    COL_COUNT = 5
    COL_LINK = 7
    COL_DROP_DOWN = 8
    COL_LOOKUP = 9
    COL_IMAGE = 10
    COL_CURRENCY = 11
    COL_ICON = 12
    COL_DATETIME = 13
    COL_ANOTHER_COLUMN = 14
    COL_DATE_STR = 15
    COL_CURRENCY_PENCE = 16
    COL_BOOLEAN = 17

    JS_RENDER_LOOKUP = 'lookupRender'

    @staticmethod
    def get_model_path(field):
        if '__' in field:
            return '__'.join(field.split('__')[:-1]) + '__'
        else:
            return ''

    def title_from_field(self):
        if type(self.field) == str and len(self.field) > 0:
            field_no_path = self.field.split('__')[-1]
            if field_no_path.find('_') > 0:
                self.title = field_no_path.replace('_', ' ').title()
            else:
                self.title = field_no_path[0]
                for letter in field_no_path[1:]:
                    if letter.isupper():
                        self.title += ' '
                    self.title += letter

    @staticmethod
    def generate_column(column_setup, start_field, model_field, **kwargs):
        if isclass(column_setup):
            column = column_setup(start_field, **kwargs)
        elif isinstance(column_setup, ColumnClassWrapper):
            return column_setup.get_class_instance(column_name=start_field, **kwargs)
        else:
            # column = ColumnDef(start_field, *args)
            column = ColumnBase(field=start_field.split('__')[-1]).get_class_instance(column_name=start_field, **kwargs)
            if model_field:
                pass
                # column.setup_from_field(model_field)
                # column.setup_args(args)
            if isinstance(column_setup, dict):
                column.column_name = start_field.split('__')[-1]
                column.setup_kwargs(column_setup)
        return column

    @classmethod
    def create_columns(cls, start_model, start_field, **kwargs):
        field_str, options = cls.extract_options(start_field)
        model, field, setup = DatatableModel.get_setup_data(start_model, field_str)
        if type(setup) != list:
            return [cls.generate_column(setup, start_field, field,  **kwargs)]
        columns = []
        for s in setup:
            columns.append(cls.generate_column(s, start_field, field, **kwargs))
        return columns

    def setup_from_field(self, field):
        self.title = field.verbose_name.title()
        field_type = type(field)
        self.column_type = ColumnDef.COL_TEXT
        if field_type == models.DateField:
            self.column_type = ColumnDef.COL_DATE_OF_DATETIME
        elif field_type == models.DateTimeField:
            self.column_type = ColumnDef.COL_DATE_OF_DATETIME
        elif (field_type == models.IntegerField or
              field_type == models.PositiveSmallIntegerField or
              field_type == models.PositiveIntegerField) and len(field.choices) > 0:
            self.column_type = ColumnDef.COL_DICT_LOOKUP
            self.options['optionText'] = {c[0]: c[1] for c in field.choices}
        elif field_type == models.BooleanField:
            self.column_type = ColumnDef.COL_BOOLEAN

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

    def __init__(self, name, *args, **kwargs):

        self.kwargs = kwargs
        self.model = None
        self.model_field = None

        name_args = name.split('|')
        if len(name_args) > 1:
            self.args = name_args[1:]
        else:
            self.args = []
        self.column_name, self.options = self.extract_options(name_args[0])

        self.model_path = self.get_model_path(self.column_name)
        self.field = self.column_name
        self.column_type = ColumnDef.COL_DEFAULT
        self.model_definitions = None
        self.annotations = None
        self.additional_columns = None
        self.column_ref = self.field
        if not hasattr(self, 'title'):
            self.title = ''
            self.title_from_field()
        self.setup_results_fn = self.setup_results
        self.data_from_results_fn = self.data_from_results
        self.setup_args(args)
        self.post_init()

    def row_result(self, data_dict, page_results):
        return self.data_from_results_fn(self, data_dict, page_results)

    def post_init(self):
        return

    def set_fields(self, field):
        if isinstance(field, (list, tuple)):
            self.field = [self.model_path + o for o in field]
        else:
            self.field = self.model_path + field

    def f(self, field):
        return F(self.model_path + field)

    def set_results_function(self, function):
        if callable(function):
            self.data_from_results_fn = function
        else:
            self.data_from_results_fn = getattr(self.model.Datatable, function)

    def url_option(self, url_name):
        if type(url_name) == tuple:
            self.options['url'] = reverse(url_name[0], args=[*url_name[1:]])
        else:
            if url_name.find('999999') == -1:
                self.options['url'] = reverse(url_name, args=[999999])
            else:
                self.options['url'] = url_name
        if self.column_type == ColumnDef.COL_DEFAULT:
            self.column_type = self.COL_LINK

    kwarg_functions = {
        'fields': set_fields,
        'results_fn': set_results_function,
        'url': url_option,
    }

    def setup_kwargs(self, kwargs):
        for a, value in kwargs.items():
            if a in self.kwarg_functions:
                self.kwarg_functions[a](self, value)
            elif hasattr(self, a):
                setattr(self, a, value)
            else:
                self.options[a] = value
        return self

    def setup_args(self, args):
        for a in args:
            if type(a) == dict:
                self.setup_kwargs(a)
            elif isinstance(a, str):
                self.title = a
            elif type(a) == int:
                self.column_type = a

    def setup_results(self, request, all_results):
        return

    @staticmethod
    def no_process(self, data, page_data):
        return data.get(self.field, '')

    @staticmethod
    def col_dict_lookup(self, data, page_data):
        return self.options['optionText'].get(data.get(self.field), '')

    @staticmethod
    def tuple_field(self, data, page_data):
        return ' '.join(str(data.get(f)) for f in self.field if data.get(f))

    @staticmethod
    def currency_field(self, data, page_data):
        try:
            return '{:.2f}'.format(data[self.field])
        except KeyError:
            return

    @staticmethod
    def currency_pence_field(self, data, page_data):
        try:
            return '{:.2f}'.format(data[self.field] / 100.0)
        except KeyError:
            return

    @staticmethod
    def format_date_time(self, data, page_data):
        try:
            date = data[self.field].strftime('%d/%m/%Y')
            time_str = data[self.field].strftime('%H:%M')
            if self.column_type == ColumnDef.COL_DATETIME and time_str != '00:00' and time_str != '01:00':
                return date + ' ' + time_str
            return date
        except AttributeError:
            return ""

    @staticmethod
    def boolean_field(self, data, page_data):
        try:
            if data[self.field]:
                return 'true'
            else:
                return 'false'
        except KeyError:
            return

    def col_date_str(self, data, page_data):
        field_data = data.get(self.field)
        if not field_data:
            return None
        return '{}/{}/{}'.format(*field_data[:10].split('-')[::-1])

    def set_row_function(self, column_type):
        render_functions = {
            ColumnDef.COL_DATE_STR: ColumnDef.col_date_str,
            ColumnDef.COL_DICT_LOOKUP: ColumnDef.col_dict_lookup,
            ColumnDef.COL_CURRENCY: ColumnDef.currency_field,
            ColumnDef.COL_CURRENCY_PENCE: ColumnDef.currency_pence_field,
            ColumnDef.COL_BOOLEAN: ColumnDef.boolean_field,
            ColumnDef.COL_DATETIME: ColumnDef.format_date_time,
            ColumnDef.COL_DATE_OF_DATETIME: ColumnDef.format_date_time,
        }
        self.data_from_results_fn = render_functions.get(column_type, ColumnDef.no_process)

    @staticmethod
    def data_from_results(self, result_dictionary, page_data):
        if isinstance(self.field, tuple):
            self.data_from_results_fn = ColumnDef.tuple_field
        else:
            self.set_row_function(self.column_type)
        return self.data_from_results_fn(self, result_dictionary, page_data)

    def style(self):
        if self.options and 'columnDefs' in self.options:
            colDefStr = self.options['columnDefs']
        else:
            colDefStr = {}
        if self.column_type == ColumnDef.COL_CURRENCY or self.column_type == ColumnDef.COL_CURRENCY_PENCE:
            colDefStr['className'] = 'dt-body-right pr-4'
        if 'mobile' in self.options and not(self.options['mobile']):
            colDefStr['mobile'] = False
        if 'hidden' in self.options and self.options['hidden']:
            colDefStr['visible'] = False
            colDefStr['searchable'] = False
        if 'pivot' in self.options and self.options['pivot']:
            colDefStr['searchable'] = True
        if 'mouseover' in self.options:
            self.options['renderfn'] = 'mouseOver'
        elif 'javascript' in self.options:
            self.options['renderfn'] = 'jsRender'
        elif self.column_type == ColumnDef.COL_LINK:
            self.options['renderfn'] = 'urlRender'
        elif self.column_type == ColumnDef.COL_ICON:
            self.options['renderfn'] = 'iconRender'
        if 'type' in self.options:
            colDefStr['type'] = self.options['type']
        if self.column_type == ColumnDef.COL_DATETIME:
            colDefStr['sType'] = 'crmdate'
        if self.column_type == ColumnDef.COL_IMAGE:
            self.options['renderfn'] = 'imageRender'
        if self.column_type == ColumnDef.COL_ANOTHER_COLUMN:
            self.options['renderfn'] = 'anotherColumn'
        if self.column_type == ColumnDef.COL_LOOKUP:
            self.options['renderfn'] = 'lookupRender'
        return colDefStr
'''


class DatatableTable:

    page_length = 100

    def __init__(self):
        self.columns = []
        self.html_id = ''
        self.table_options: Dict[KT, VT] = {}

        self.orgdata = None
        self.model = None

        # django query attibutes
        self.filter = {}
        self.exclude = {}
        self.distinct = []

        # javascript datatable attributes
        self.order_by = []
        self.js_filter_list = []

        self.max_records = None
        self.table_classes = ['display', 'compact', 'smalltext', 'table-sm', 'table', 'w-100']
        self.table_options['pageLength'] = self.page_length
        self.omit_columns = []

    def add_js_filters(self, name_or_template, column_ids, **kwargs):
        if type(column_ids) == str:
            column_ids = [column_ids]
        for c in column_ids:
            self.js_filter_list.append(DatatableFilter(name_or_template, self, column=self.find_column(c)[0], **kwargs))

    def js_filter(self, name_or_template, column_id, **kwargs):
        return DatatableFilter(name_or_template, self, column=self.find_column(column_id)[0], **kwargs)

    def get_query(self, **kwargs):
        annotations = {}
        for c in self.columns:
            if c.annotations:
                annotations.update(c.annotations)
        if 'single' in kwargs and 'pk' in kwargs:
            self.filter['pk'] = kwargs['pk']

        query = (self.model.objects.annotate(**annotations).filter(**self.filter)
                 .exclude(**self.exclude).values(*self.fields())
                 .order_by(*self.order_by))
        if self.distinct:
            query = query.distinct(*self.distinct)
        if self.max_records:
            query = query[:self.max_records]
        return query

    def sort(self, *columns):
        self.table_options['order'] = []
        for c in columns:
            sort_order = 'asc'
            if c[0] == '-':
                sort_order = 'desc'
                c = c[1:]
            self.table_options.setdefault('order', []).append([self.find_column(c)[1], sort_order])

    def row_color(self, column, *option_colors):
        self.table_options.setdefault('rowColor', []).append(
            {'colRef': column, 'values': {o[0]: o[1] for o in option_colors}})

    def add_column_options(self, column_ref, options):
        if type(column_ref) == str:
            column_ref = [column_ref]
        for c in self.columns:
            if c.column_ref in column_ref:
                c.setup_kwargs(options)

    def find_column(self, column_name):
        for n, c in enumerate(self.columns):
            if c.column_name == column_name:
                return c, n

    def change_column(self, field, column_type, options):
        for c in self.columns:
            if c.field == field:
                c.column_type = column_type
                c.add_options(options)
                return

    @staticmethod
    def generate_column(column_setup, start_field, model_field, **kwargs):
        if isclass(column_setup):
            column = column_setup(**kwargs, column_name=column_setup.__name__)
        elif isinstance(column_setup, ColumnBase):
            return column_setup.get_class_instance(column_name=start_field, **kwargs)
        else:
            # column = ColumnDef(start_field, *args)
            column = ColumnBase(field=start_field.split('__')[-1]).get_class_instance(column_name=start_field, **kwargs)
            if model_field:
                field_type = type(model_field)
                if field_type == models.DateField:
                    column.row_result =  MethodType(format_date_time, column)
            if isinstance(column_setup, dict):
                column.column_name = start_field.split('__')[-1]
                column.setup_kwargs(column_setup)
        return column

    def create_columns(self, start_model, start_field, **kwargs):
        field_str, options = ColumnBase.extract_options(start_field)
        model, field, setup = DatatableModel.get_setup_data(start_model, field_str)
        if type(setup) != list:
            return [self.generate_column(setup, start_field, field,  **kwargs)]
        columns = []
        for s in setup:
            columns.append(self.generate_column(s, start_field, field, **kwargs))
        return columns

    def get_columns(self, column, **kwargs):
        if isinstance(column, str):
            if column in self.omit_columns:
                return []
            return self.create_columns(self.model, column, **kwargs)
        elif isinstance(column, ColumnBase):
            if column.column_name in self.omit_columns:
                return []
            return [column]
        else:
            return self.create_columns(self.model, column[0], **column[1])

    def add_columns(self, *columns, **kwargs):
        for c in columns:
            new_columns = self.get_columns(c, **kwargs)
            for add_col in new_columns:
                self.columns.append(add_col)
                # if add_col.additional_columns:
                #    self.add_columns(*add_col.additional_columns, **kwargs)

    def fields(self):
        fields = []
        for c in self.columns:
            if c.field and 'calculated' not in c.options:
                if isinstance(c.field, (tuple, list)):
                    for f in c.field:
                        if f not in fields:
                            fields.append(f)
                else:
                    if c.field not in fields:
                        fields.append(c.field)
        return fields

    def all_names(self):
        return [c.column_name for c in self.columns]

    def all_refs(self):
        return [c.column_ref for c in self.columns]

    def all_titles(self):
        return [str(c.title) for c in self.columns]

    @staticmethod
    def tag_array(array, tag_str):
        return ''.join([tag_str.format(e) for e in array])

    def search_boxes(self):
        return render_to_string('datatables/search_boxes.html', {'table': self})

    def html_setup(self):
        footer = ''
        title_class = ''
        if self.table_options.get('no_titles', False):
            title_class = ' class="d-none"'
        titles = ''.join([f'<th>{t}</th>' for t in self.all_titles()])
        if not self.table_options.get('nofooter', False):
            footer = f'<tfoot><tr>{titles}</tr></tfoot>'
        return (
            f'<table id="{self.html_id}" class="{" ".join(self.table_classes)}">'
            f'<thead><tr{title_class}>{titles}</tr>{self.search_boxes()}</thead>{footer}</table>'
        )

    def javascript_setup(self):
        return self.html_setup() + '<script>' + self.javascript() + '</script>'

    def javascript(self):
        col_def_array = []
        col_options = []

        count = 0
        for c in self.columns:
            col_def = c.style()
            col_def['targets'] = count
            col_def['name'] = c.column_name
            col_def_array.append(col_def)
            count += 1
            col_options.append(dict(c.options))

        if 'rowColor' in self.table_options:
            if isinstance(self.table_options['rowColor'], list):
                for rc in self.table_options['rowColor']:
                    if 'colRef' in rc:
                        rc['column'] = self.all_refs().index(rc['colRef'])
            if 'colRef' in self.table_options['rowColor']:
                self.table_options['rowColor']['column'] = self.all_refs().index(self.table_options['rowColor']
                                                                                 ['colRef'])

        self.table_options['media'] = settings.MEDIA_URL
        table_vars = {
            'colDefs': col_def_array,
            'field_ids': self.all_names(),
            'colOptions': col_options,
            'tableOptions': self.table_options,
            'titles': self.all_titles(),
        }

        col_def_str = json.dumps(table_vars)
        col_def_str = col_def_str.replace('"&', "")
        col_def_str = col_def_str.replace('&"', "")

        if self.orgdata is not None:
            orgdata = ',' + self.orgdata
        else:
            orgdata = ''
        inittable = (f'django_datatables.DataTables.{self.html_id}= new PythonTable("{self.html_id}", '
                     f'local_colDefs_{self.html_id}, "{self.ajax}" {orgdata});')

        return 'local_colDefs_' + self.html_id + '=' + col_def_str + ";" + inittable

    def get_table_array(self, request, results, show_hidden=True):
        json_list = []
        page_results = {}
        for c in self.columns:
            c.setup_results(request, page_results)
        for data_dict in results:
            new_list = []
            for c in self.columns:
                if show_hidden or not c.options.get('hidden'):
                    try:
                        new_list.append(c.row_result(data_dict, page_results))
                    except KeyError:
                        new_list.append('')
            json_list.append(new_list)
        return json_list

    def get_json(self, request, results, set_vars=None):
        if len(results) > 0 and isinstance(results[0], tuple):
            return_data = {'data': results}
        else:
            return_data = {'data': self.get_table_array(request, results)}
        if set_vars is not None:
            return_data['set_vars'] = set_vars
        return json.dumps(return_data, indent=None, default=str)


class DatatableView(TemplateView):
    model = None

    def __init__(self, *args, **kwargs):
        super(DatatableView, self).__init__(*args, **kwargs)
        self.table = DatatableTable()
        self.table.model = self.model
        self.table.html_id = type(self).__name__.lower()
        self.dispatch_context = None

    def post_table_json(self, **kwargs):
        return self.table.get_query(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.table.ajax = request.get_full_path() + '?json'
        self.dispatch_context = detect_device(request)
        self.setup_table()
        return super(DatatableView, self).dispatch(request, *args, **kwargs)

    def add_options(self, new_options):
        self.table.table_options.update(new_options)

    def render_to_response(self, context, **response_kwargs):
        if self.template_name is None:
            return HttpResponse(self.table.javascript_setup())
        return super(DatatableView, self).render_to_response(context, **response_kwargs)

    @staticmethod
    def graph_data(**kwargs):
        return None

    @staticmethod
    def locked():
        return False

    def post(self, request, *args, **kwargs):

        self.table.ajax = request.get_full_path()+'?json'
        if request.GET.get('json', None) is not None:
            results = self.post_table_json(**kwargs)
            if self.locked():
                secure_fields = [c.field for c in self.table.columns if c.options.get('secure')]
                if secure_fields:
                    for r in results:
                        for f in secure_fields:
                            data = r.get(f)
                            if data:
                                r[f] = '<i class="fas fa-key"></i>'
            return HttpResponse(self.table.get_json(request, results, self.graph_data(**kwargs)),
                                content_type='application/json')
        return None
    """
    def get(self, request, *args, **kwargs):
        self.table.ajax = request.get_full_path()+'?json'
        if request.GET.get('json', None) is not None:
            '''
            # ***************************************************
            # Uncomment for benchmarking SQL calls for datatables
            # ***************************************************
            a = getJson(self.table, self.post_table_json(**kwargs))
            context = self.get_context_data(**kwargs)
            self.template_name = 'blank.html'
            return self.render_to_response(context)
            '''
            return self.table_json(**kwargs)
        else:
            context = self.get_context_data(**kwargs)
            return self.render_to_response(context)
    """
    def get_context_data(self, **kwargs):
        context = super(DatatableView, self).get_context_data(**kwargs)
        context['datatable'] = self.table
        context.update(self.add_to_context(**kwargs))
        return context

    def add_to_context(self, **kwargs):
        return {}

    def add_columns(self, *columns, **kwargs):
        self.table.add_columns(*columns, **kwargs)

    @abstractmethod
    def setup_table(self):
        pass


def simple_table(table):
    table.table_options['domOptions'] = 't'
    table.table_options['no-col-search'] = True
    table.table_options['nofooter'] = True
    table.table_options['pageLength'] = 400
