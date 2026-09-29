import copy
import json
import re
from types import MethodType
from typing import Dict, Any

from django.db.models import Q
from django.db.models.expressions import Case, F, Subquery, When
from django.forms.widgets import Select

from django_datatables.helpers import render_replace


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

    # Default so getattr/hasattr are always safe before __init__ assigns them.
    _search_field = None
    search = None
    edit_type = None

    # Which element of a field_array row_result the Excel / clipboard export should use.
    # None exports the value as-is; link-style columns whose row_result is [ref, text] set
    # this to 1 so the export gets the displayed text rather than the row's pk.
    excel_array_index = None

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
        return self.__class__(column_name=column_name, **{**self.kwargs, **kwargs})

    def extract_args(self):
        args = self.column_name.split('|')
        self.column_name = args[0]
        return args[1:]

    def __init__(self, field=None, **kwargs):
        if not self.initialise(locals()):
            return
        # Remove  ._$ characters from beginning of name and set appropriate options
        self._column_name = None
        self.column_defs = {}
        self.column_name, options = self.extract_options(kwargs.get('column_name', ''))
        self.options: Dict[str, Any] = options
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
        # Optional per-column server-side search overrides (see get_search_filter).
        self.search_field = kwargs.pop('search_field', None)
        self.search = kwargs.pop('search', None)
        self.args = self.extract_args()
        self.title = self.title_from_name(self.column_name)
        self.column_type = 0
        self._annotations = None
        self._annotations_value = None
        self._aggregations = None
        self.additional_columns = []
        self.spreadsheet = kwargs.pop('spreadsheet', {})
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
            # row_result is now [id, label] - export the label, not the id.
            self.excel_array_index = 1
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

    # Parts of an annotation that resolve their own field references, so model_path must not be
    # applied inside them: a Subquery (an Exists is one) runs against its own model, and the
    # conditions of a Case are written by the column, which is where the path belongs.
    opaque_annotation_expressions = (Subquery, Case, When)

    def _prefix_annotation_fields(self, expression, visited):
        """Grow every field reference inside one annotation by model_path.

        An annotation is written against the model that declares it - Sum('total_sell') on a
        column of that model - so a column pulled in through a relation needs the references in
        it rewritten to that relation path: Sum('batch__total_sell').

        An F (an OuterRef is one) is the only thing that names a field, so it is the only thing
        rewritten; everything else is walked to find the ones that do. Notably an aggregate is
        not one despite having a ``name`` attribute - Sum('x').name is 'Sum' - and taking that
        for a field name renamed the aggregate instead of reaching the reference inside it.

        ``visited`` carries the ids already rewritten, because an expression assembled from a
        reused sub-expression holds the same object at several places in the tree and would
        otherwise have the path applied to it once per place.
        """
        for source_expression in expression.get_source_expressions():
            if source_expression is None or id(source_expression) in visited:
                continue
            if isinstance(source_expression, self.opaque_annotation_expressions):
                continue
            visited.add(id(source_expression))
            if isinstance(source_expression, F):
                source_expression.name = self.model_path + source_expression.name
            elif hasattr(source_expression, 'get_source_expressions'):
                self._prefix_annotation_fields(source_expression, visited)

    def _set_annotations(self, value):
        annotations = copy.deepcopy(value)
        if self.model_path:
            new_annotations = {}
            # One visited set for the whole dict: deepcopy keeps a sub-expression shared between
            # two annotations shared, so it must not be rewritten once per annotation either.
            visited = set()
            for k in annotations:
                new_annotations[self.model_path + k] = annotations[k]
                self._prefix_annotation_fields(new_annotations[self.model_path + k], visited)
            annotations = new_annotations
        for f in annotations:
            if self.field is None:
                self._field = f
            elif isinstance(self.field, str):
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
            self._field = list(self._field) + [self.model_path + field]

    @property
    def search_field(self):
        return self._search_field

    @search_field.setter
    def search_field(self, value):
        # None  -> fall back to `field` (see _search_paths)
        # False -> explicitly not searchable / not sortable
        # str / list -> ORM path(s), model_path-prefixed once (like `field`)
        if value is None or value is False:
            self._search_field = value
        elif isinstance(value, (list, tuple)):
            self._search_field = [self.model_path + f for f in value]
        else:
            self._search_field = self.model_path + value

    def _search_paths(self):
        """Already-prefixed ORM path(s) driving the simple icontains search and ordering.

        ``search_field=False`` -> ``[]``; an explicit ``search_field`` -> that; a single
        string ``field`` on a non-calculated column -> ``[field]``; otherwise ``[]``
        (list field / calculated / no field).
        """
        if self._search_field is False:
            return []
        if self._search_field:
            if isinstance(self._search_field, (list, tuple)):
                return list(self._search_field)
            return [self._search_field]
        if self.field and isinstance(self.field, str) and 'calculated' not in self.options:
            return [self.field]
        return []

    def get_search_filter(self, value):
        """Return a ``Q`` for a header/global server-side search of ``value`` on this column,
        or ``None`` if the column is not searchable.

        Override in a subclass (or pass a ``search=`` callable) for complex logic — exact
        match, ranges, negation, OR across related fields, etc. The default ORs ``icontains``
        across ``_search_paths``.
        """
        if self.search is not None:
            result = self.search(value)
            return Q(**result) if isinstance(result, dict) else result
        fields = self._search_paths()
        if not fields:
            return None
        q = Q()
        for f in fields:
            q |= Q(**{f'{f}__icontains': value})
        return q

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
        pass

    def html_result(self, data_dict, page_results):
        from django.utils.html import conditional_escape
        value = self.row_result(data_dict, page_results)
        if value is None:
            return ''
        return conditional_escape(str(value))

    def default_row_result(self, data_dict, page_results):
        """The value the column would produce without a row_result override,
        for subclasses that want to post-process the default result."""
        if self.options.get('field_array'):
            return self.__list_row_result(self, data_dict, page_results)
        return self.__row_result(self, data_dict, page_results)

    @staticmethod
    def __list_row_result(self, data_dict, _page_results):
        return [data_dict.get(f) for f in self.field]

    @staticmethod
    def __row_result(self, data_dict, _page_results):
        if self.options.get('choices'):
            return self.options['choices'].get(data_dict.get(self.field))
        if self.blank:
            ret_val = data_dict.get(self.field)
            if ret_val is None or ret_val == '':
                return self.blank
            return ret_val
        return data_dict.get(self.field)

    def style(self):
        col_def_str = dict(self.column_defs)
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
        if isinstance(name, str) and len(name) > 0:
            field_no_path = name.split('/')[-1].split('__')[-1]
            if '_' in field_no_path:
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

    def excel(self, value):
        """Convert a row_result value into something openpyxl can write.

        Subclasses whose row_result is not already a plain scalar should override this
        (and optionally add xl_style) rather than let the value fall through to str().
        """
        if self.excel_array_index is not None and isinstance(value, (list, tuple)):
            index = self.excel_array_index
            value = value[index] if len(value) > index else None
        if isinstance(value, (int, float, str)):
            return value
        elif value is None:
            return ''
        return str(value)

    def xl_dont_show(self):
        """Return True to omit this column from the Excel / clipboard export."""
        return False

    def spreadsheet_init(self):
        column_init = {'title': self.title, 'width': self.column_defs.get('width', 100)}
        column_init.update(self.spreadsheet)

        def allow_javascript(key_pair):
            return key_pair.replace('"', '') if key_pair.startswith(' "editor":') else key_pair

        return '{' + ','.join([(allow_javascript(v))
                               for v in json.dumps(column_init).strip('{').strip('}').split(',')]) + '}'
