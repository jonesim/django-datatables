from django.db.models import Count

from datatable_examples import models
from datatable_examples.views.base import ManualPage
from django_datatables.columns import ColumnBase
from django_datatables.datatables import DatatableView
from django_datatables.helpers import render_replace
from django_datatables.plugins.colour_rows import ColourRows


class RenderFunctions(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Render Functions'
    code_examples = ['setup_table', 'get_table_query']

    @staticmethod
    def setup_table(table):

        lookup = [
            [1, 'one'],
            [2, 'two'],
            [3, 'three'],
            [4, 'four'],
            [5, 'five'],
            [6, 'six'],
            [7, 'seven'],
            [8, 'eight'],
            [9, 'nine'],
            [0, 'zero'],
        ]

        coloured_lookup = [
            [1, ['one', 'secondary']],
            [2, ['two', 'primary']],
            [3, ['three', 'warning']],
            [4, ['four', 'secondary']],
            [5, ['five', 'secondary']],
            [6, ['six', 'secondary']],
            [7, ['seven', 'secondary']],
            [8, ['eight', 'secondary']],
            [9, ['nine', 'secondary']],
            [0, ['zero', 'secondary']],
        ]

        table.add_columns(
            'id',
            ('id', {'title': 'Simple Replace', 'render': [render_replace(column='id', html='* %1%')]}),
            ('id', {'title': 'HTML first render followed by Replace', 'render': [{'function': 'Html', 'html': '* %1%'},
                                                                                 render_replace(column='id')]}),
            ('_array', {'title': 'Repeated replace on list', 'render': [render_replace(column='array', html='- %1%')]}),
            ('_array1', {'title': 'Replace with indexed item in list', 'field_array': True,
                         'render': [render_replace(column='array:1', html=': %1%')]}),
            ('_array1', {'title': 'Replace with alternative for null item', 'field_array': True,
                         'render': [render_replace(column='array:1', html=': %1%',
                                                   null_value='@ none',)]}),
            ('_array1', {'title': 'Alternative result for gte (>) 50 ', 'field_array': True,
                         'render': [render_replace(column='array:1', html=': %1%', gte=50, alt_html='GTE 50 : %1%')]}),
            ('_array1', {'title': 'Alternative result for gte (>) 50 and then gte 100', 'field_array': True,
                         'render': [render_replace(column='array:1', html=': %1%', gte=50, alt_html='GTE 50 : %1%'),
                                    render_replace(column='array:1', gte=100, alt_html='GTE 100 : %1%')]}),
            ('_array1', {'title': 'Alternative result for eq (=) 50 and then eq 100', 'field_array': True,
                         'render': [render_replace(column='array:1', html=': %1%', eq=50, alt_html='EQ 50: %1%'),
                                    render_replace(column='array:1', eq=110, alt_html='EQ 110 : %1%')]}),

            ('_array', {'title': 'Replace with multiple items from list', 'field_array': True,
                        'render': [{'function': 'Replace', 'var': ['%1%', '%2%'], 'html': 'first %1% Second %2%'}]}),
            ('_max10', {'title': 'Demo field (Max10)'}),
            ('_max10', {'title': 'Replacelookup function on Max10',
                        'render': [{'function': 'ReplaceLookup', 'html': 'html %1%', 'var': '%1%'}], 'lookup': lookup}),
            ('_max10', {'title': 'Replacelookup function with gte', 'render': [
                {'function': 'ReplaceLookup', 'html': 'html %1%', 'var': '%1%',
                 'alt_html': 'BIG %1%', 'gte': 4}
            ], 'lookup': lookup}),
            ('_array', {'title': ' MergeArray function', 'field_array': True, 'render': [{'function': 'MergeArray'}]}),
            ('_array', {'title': ' MergeArray function with different separator', 'field_array': True,
                        'render': [{'function': 'MergeArray', 'separator': '#'}]}),
            ('_max10', {'title': 'Replacelookup using 2 items from an array one indicating colour', 'render': [
                {'function': 'ReplaceLookup', 'html': '<span class="badge badge-%2%">%1%</span>', 'var': ['%1%', '%2%']}
            ], 'lookup': coloured_lookup}),

            ('_array', {'field_array': True, 'render': [render_replace(column='array:1', html='%1%')]})
        )

    @staticmethod
    def get_table_query(table, **kwargs):
        results = table.get_query(**kwargs)
        for r in results:
            if r['id'] % 2:
                r['array'] = [r['id'], r['id'] * 10]
            r['max10'] = r['id'] % 10
        return results

    def add_to_context(self, **kwargs):
        return {'description': (
            'The client-side render functions — <b>Replace</b>, <b>ReplaceLookup</b>, <b>Html</b> and '
            '<b>MergeArray</b> — build cell HTML in the browser from raw row data. Renders can chain, '
            'substitute multiple variables, index into list values (<code>column:1</code>), and switch '
            'to an alternative result on <code>gte</code>/<code>eq</code> comparisons or null values. '
            'The <code>render_replace</code> helper builds the most common descriptor. The row data '
            'here is post-processed in <code>get_table_query</code> to add list and bounded values to '
            'render against.'
        )}


class HtmlRendering(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Server vs Client HTML'

    @staticmethod
    def badge(_column, data_dict, _page_results):
        return f'<span class="badge badge-secondary">{data_dict.get("people")}</span>'

    @staticmethod
    def people_band(_column, data_dict, _page_results):
        return 'high' if data_dict.get('people') > 2 else 'low'

    def setup_table(self, table):
        table.add_columns(
            'name',
            ColumnBase(column_name='CustomResultFunction', field='people', row_result=self.badge,
                       annotations={'people': Count('person__id')}, title='Send HTML'),
            ColumnBase(column_name='Range', field='people', row_result=self.people_band, hidden=True),
            ColumnBase(column_name='people', title='HTML generated in JS', field='people', render=[
                {'var': '%1%', 'column': 'people', 'html': '<span class="badge badge-primary">%1%</span>',
                 'function': 'Replace'},
               ]),
        )
        table.add_plugin(ColourRows, [{'column': 'Range', 'values': {'high': 'table-danger', 'low': 'table-warning'}}])
        table.sort('-people')

    def add_to_context(self, **kwargs):
        return {'description': (
            'Two ways to put HTML in a cell: a <code>row_result</code> function builds it on the server '
            'and sends the finished string, while a <code>render</code> descriptor sends only the value '
            'and builds the HTML in the browser — less data over the wire for the same output. '
            'The hidden <code>Range</code> column drives the <code>ColourRows</code> plugin, which '
            'applies a CSS class to each row from a column value; the rows are sorted by the '
            '<code>people</code> annotation.'
        )}


class ChoiceRendering(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Choices & Null Values'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            ('id', {'column_defs': {'width': '30px'}}),
            'name',
            ColumnBase(column_name='title', field='person__title',
                       choices=dict(models.Person._meta.get_field('title').choices),
                       render=[render_replace(html='ABC -%1%- DFG', column='title')]),
            ColumnBase(column_name='Title', field=['person__title', 'person__first_name'],
                       render=[{'function': 'Replace', 'html': '<span class="badge badge-success"> %1% </span>',
                                'column': 'Title:0', 'null_value': '<span class="badge badge-primary"> %2% </span>',
                                'var': '%1%'},
                               {'function': 'Replace', 'column': 'Title:1',  'var': '%2%'}]),
        )
        table.table_options['row_href'] = [render_replace(column='id', html='javascript:console.log("%1%")')]

    def add_to_context(self, **kwargs):
        return {'description': (
            'A <code>choices</code> dict maps stored values to their display labels before rendering. '
            'The second column shows <code>null_value</code>: when the title is missing, the render '
            'falls back to alternative HTML built from the person\'s first name. '
            '<code>row_href</code> makes the whole row a link — here it just logs the id to the '
            'browser console.'
        )}
