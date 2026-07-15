from django.db.models import Count
from django.forms.fields import CharField

from datatable_examples import models
from datatable_examples.views.base import ManualPage
from django_datatables.columns import ColumnBase, DatatableColumn, DateColumn
from django_datatables.datatables import DatatableView
from django_datatables.filters import PythonPivotFilter
from django_datatables.modal_filter.filter_fields import FilterModelMultipleChoiceField
from django_datatables.modal_filter.mixins import DatatableFilterField, DatatableFilterMixin


class PivotSelect2Filters(ManualPage, DatatableView):
    model = models.Person
    page_title = 'Pivot & Select2 Filters'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            ('id', {'options': {'initial_filter': {'1': False, '102': False}}}),
            'first_name',
            ('company__name', {'title': 'Company Name'}),
            'title_model',
        )
        table.add_js_filters('select2', 'company__name')
        table.add_js_filters('pivot', 'title_model')
        table.add_js_filters('pivot', 'id')
        table.add_js_filters(PythonPivotFilter, 'first_name', filter_title='First name (fixed list)',
                             filter_list=[('Starts with T', 'T'), ('Other', 'other')])

    def add_to_context(self, **kwargs):
        return {'description': (
            'The two everyday client-side filters. A <b>pivot</b> filter shows a checkbox per distinct '
            'column value with live counts of matching rows; a <b>select2</b> filter offers the same '
            'values in a searchable dropdown, better when there are many. An '
            '<code>initial_filter</code> option pre-unchecks values when the page loads — ids 1 and '
            '102 start filtered out. <code>PythonPivotFilter</code> is a pivot variant whose options '
            'are a fixed list of <code>(label, value)</code> pairs defined in Python, with unlisted '
            'values collected under an <code>other</code> bucket.'
        )}


class TagFilter(ManualPage, DatatableView):
    model = models.Company
    template_name = 'datatable_examples/wide_filter.html'
    page_title = 'Tag Filter'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'name',
            'TagList',
            ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
        )
        table.add_js_filters('tag', 'TagList')

    def add_to_context(self, **kwargs):
        return {'description': (
            'A tag filter on a many-to-many column. Each tag cycles through four states as it is '
            'clicked: neutral, <b>include</b> (rows with any included tag), <b>required</b> (rows must '
            'have every required tag), and <b>exclude</b>. The counts update live as other filters and '
            'searches change the result set.'
        )}


class DateFilter(ManualPage, DatatableView):
    model = models.Person
    page_title = 'Date Filter'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'first_name',
            'surname',
            DateColumn('date_entered', column_name='Date'),
        )
        table.add_js_filters('date', 'date_entered')

    def add_to_context(self, **kwargs):
        return {'description': (
            'A date-range filter block with from/to pickers, applied client-side to the '
            '<code>date_entered</code> column. <code>DateColumn</code> formats the value as '
            'dd/mm/yyyy while keeping it sortable.'
        )}


class TotalsFilter(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Totals Filter'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'name',
            ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
        )
        table.add_js_filters('totals', 'people', filter_title='Number of People', collapsed=False)

    def add_to_context(self, **kwargs):
        return {'description': (
            'A totals filter behaves like a pivot filter, but instead of counting rows it sums the '
            'column — the Filtered and Total figures here are the number of people per company, '
            'recalculated as rows are filtered in and out.'
        )}


class CollapseButton(DatatableColumn):

    plus = 'fas fa-plus-circle'
    minus = 'fas fa-minus-circle'
    expand_button = '<a onclick="show_tree(this)"><i class="{}"></i></a>'

    def col_setup(self):
        self.options['render'] = [
            {'var': '%1%', 'html': '%1%', 'function': 'ReplaceLookup'},
        ]
        self.options['lookup'] = (('+', self.expand_button.format(self.plus)),
                                  ('-', self.expand_button.format(self.minus)),
                                  (' ', ' '))
        self.options['no_col_search'] = True
        self.title = ''


class RowTree(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Row Expansion (Tree)'
    code_examples = ['setup_table', 'get_table_query']

    @staticmethod
    def setup_table(table):
        table.add_columns(
            CollapseButton(column_name='collapsed', field='collapsed'),
            '.level',
            '.id',
            '.person_id',
            ColumnBase(column_name='name', field='name', column_defs={'orderable': False}),
            'first_name',
            'surname',
        )
        table.sort('id', 'level')
        table.add_js_filters('expand', 'level', id_column='id')
        table.column('first_name').column_defs['orderable'] = False
        table.column('surname').column_defs['orderable'] = False
        table.column('collapsed').column_defs['orderable'] = False

    @staticmethod
    def get_table_query(table, **kwargs):
        query = list(table.model.objects.values('id', 'name'))
        people = list(models.Person.objects.values('id', 'company_id', 'first_name', 'surname', 'company__name'))
        for q in query:
            q['level'] = 0
            q['collapsed'] = '+'

        for p in people:
            p['person_id'] = p['id']
            p['id'] = p['company_id']
            p['level'] = 1
            p['collapsed'] = ' '
            p['name'] = '<span class="text-secondary pl-2">' + p['company__name'] + '</span>'

        query += people
        return query

    def add_to_context(self, **kwargs):
        return {'description': (
            'Expandable parent/child rows built with the <b>expand</b> filter. '
            '<code>get_table_query</code> supplies a combined list of companies (level 0) and their '
            'people (level 1); the filter shows level-0 rows and reveals a parent\'s children when its '
            '+ button — a custom column rendering an expand/collapse icon — is clicked.'
        )}


class CustomJsFilter(ManualPage, DatatableView):
    model = models.Tally
    template_name = 'datatable_examples/custom_filter.html'
    page_title = 'Custom JavaScript Filter'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'cars',
            'vans',
            'buses',
        )

    def add_to_context(self, **kwargs):
        return {'description': (
            'Filter blocks are templates, so an entirely custom one can be added with the '
            '<code>{% filter_template %}</code> tag. This one registers a JavaScript object with '
            '<code>django_datatables.add_filter</code> that implements the calculation hooks '
            '(<code>init_calcs</code>, <code>add_calcs</code>, <code>refresh</code>) to show the sum, '
            'mean, and standard deviation of the first column — recalculated live as the table is '
            'searched. See the <i>Source Code</i> button for the template.'
        )}


class SearchBoxes(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Search Boxes'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'name',
            ColumnBase(column_name='dissolved',
                       field='dissolved',
                       col_search_select=[['true', 'True'], ['false', 'False']]),
            ColumnBase(column_name='order', field='order', no_col_search=True)
        )

    def add_to_context(self, **kwargs):
        return {'description': (
            'Per-column search controls in the table header. The default is a text box; '
            '<code>col_search_select</code> replaces it with a dropdown of fixed values, and '
            '<code>no_col_search</code> removes it for a column.'
        )}


class ModalFilter(DatatableFilterMixin, ManualPage, DatatableView):
    model = models.Company
    page_title = 'Modal Filter'

    filter_fields = [
        DatatableFilterField('Company Name',
                             CharField(help_text='Name contains', required=False),
                             datatable_field='name__contains'),
        DatatableFilterField('Tags',
                             FilterModelMultipleChoiceField(queryset=models.Tags.objects.all()),
                             datatable_field='tags__in')
    ]

    def setup_menu(self):
        self.add_menu('menu', 'buttons').add_items(*self.filter_menu_items())
        super().setup_menu()

    def setup_table(self, table):
        table.add_columns(
            ('id', {'column_defs': {'width': '30px'}}),
            'name',
            'TagList',
            ('dissolved', {'choices': ['yes', 'no']}),
        )
        self.add_modal_filter(table)

    def add_to_context(self, **kwargs):
        return {'description': (
            '<code>DatatableFilterMixin</code> adds an advanced filter dialog built from '
            '<code>filter_fields</code> — each is a Django form field mapped to an ORM lookup such as '
            '<code>name__contains</code> or <code>tags__in</code>. The chosen filter state is base64-'
            'encoded into the URL, so a filtered view can be bookmarked or shared; the menu shows the '
            'active filter and a clear button.'
        )}
