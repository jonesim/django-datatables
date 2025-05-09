import csv
import json

from datatable_examples import models
from datatable_examples.models import Tags
from datatable_examples.views.menu import MainMenu
from django.db.models import Count, ExpressionWrapper, FloatField, F
from django.db.models.functions import NullIf
from django.forms.fields import CharField
from django.http import HttpResponse

from django_datatables.columns import ColumnLink, ColumnBase, DatatableColumn, ManyToManyColumn, DateColumn
from django_datatables.datatables import DatatableView
from django_datatables.downloads.clipboard import ClipboardCopy
from django_datatables.downloads.excel_download import ExcelDownload
from django_datatables.helpers import row_button, render_replace
from django_datatables.modal_filter.filter_fields import FilterModelMultipleChoiceField
from django_datatables.modal_filter.mixins import DatatableFilterMixin, DatatableFilterField
from django_datatables.plugins.colour_rows import ColourRows
from django_datatables.plugins.column_totals import ColumnTotals
from django_datatables.plugins.reorder import Reorder
from django_datatables.reorder_datatable import ReorderDatatableView


class NumberEdit(DatatableColumn):

    def row_result(self, data_dict, _page_results):
        return '<form><input style="text-align:right" type="number" name="count" onblur=django_datatables.b_r(this) ></form>'


class NumberEdit2(DatatableColumn):

    def row_result(self, data_dict, _page_results):
        return '<form><input style="text-align:right" type="number" name="count2" onblur=django_datatables.b_r(this) value=4></form>'




class Example1(DatatableFilterMixin,ExcelDownload, ClipboardCopy,  MainMenu, DatatableView):
    model = models.Company

    filter_fields = [
        DatatableFilterField('Company Name', CharField(help_text='Name contains', required=False), datatable_field='name__contains'),
        DatatableFilterField('Tags', FilterModelMultipleChoiceField(queryset=Tags.objects.all()), datatable_field='tags__in')

    ]

    def setup_menu(self):
        self.add_menu('menu', 'buttons').add_items(*self.filter_menu_items(), self.download_menu_item(), self.clipboard_menu_item())
        super().setup_menu()

    def setup_table(self, table):
        table.add_columns(
            ('id', {'column_defs': {'width': '30px'}}),
            NumberEdit,
            NumberEdit2,
            ColumnBase(column_name='BasicButton', render=[row_button('toggle_tag', 'toggle TAG1')]),
            'name',
            # 'Tags',
            # ('dissolved', {'choices': ['yes', 'no']}),
            # ColumnLink(column_name='peoplex', field=['id', 'name'], url_name='example2'),
            # ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
            # ColumnLink(column_name='view_company', field=['id', 'name'],  url_name='example2'),
            # ColumnLink(column_name='view_company_icon', link_ref_column='id', url_name='example2', width='10px',
            #            link_html='<button class="btn btn-sm btn-outline-dark"><i class="fas fa-building"></i></button>'
            #            ),
            # 'reverse_tag',
            # ManyToManyColumn(column_name='DirectTag', field='direct_tag__tag_direct', model=models.Company,
            #                  html='<span class="badge badge-primary"> %1% </span>'),
        )
        table.column('name').column_defs['orderable'] = False
        table.add_plugin(ColourRows, [{'column': 'id', 'values': {'1': 'table-danger'}}])
        table.ajax_data = False
       # table.add_js_filters('tag', 'Tags')
       # table.add_js_filters('totals', 'people', filter_title='Number of People', collapsed=False)
       #  add_save_filters(table, self.request.user)
        # table.add_js_filters('tag', 'DirectTag')
        # table.table_options['row_href'] = [ajax_command('send_row')]
        table.table_options['no_col_search'] = True
        table.table_options['pageLength'] = '22'
        table.max_records = 94
        self.add_modal_filter(table)

        # table.table_options['scrollX'] = True
        # table.table_options['row_href'] = [render_replace(column='id', html='javascript:console.log("%1%")')]
        table.add_plugin(ColumnTotals, {'id': {'sum': 'over1000'}}, template='add_sum_calc.html')
#
    def row_column(self, row_data, inputs, **kwargs):
        print (row_data, inputs )
        return self.command_response('null')

class Example2(MainMenu, ExcelDownload, ClipboardCopy, DatatableView):
    model = models.Person
    template_name = 'datatable_examples/csv_button_table.html'
    ajax_commands = ['row', 'column']

    def setup_menu(self):
        self.add_menu('menu', 'buttons').add_items(self.download_menu_item(), self.clipboard_menu_item())
        super().setup_menu()


    def column_get_csv(self, **kwargs):

        # Does not filter out hidden columns but can easily be modified
        column_data = json.loads(kwargs['column_data'])
        table = self.tables[kwargs['table_id']]
        self.setup_tables(table_id=table.table_id)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="test.csv"'
        table.filter['id__in'] = column_data
        results = table.get_table_array(self.request, table.get_query())
        writer = csv.writer(response)
        writer.writerow(table.all_titles())
        for r in results:
            writer.writerow(r)
        return response

    def setup_table(self, table):
        table.edit_fields = ['company__name']
        table.edit_options = {'company__name': {'select2': True}}

        table.add_columns(
            'id',
            'first_name',
            ('company__name', {'title': 'Company Name'}),
            'company__collink_1'
        )
        if 'pk' in self.kwargs:
            table.filter = {'company__id': self.kwargs['pk']}
        table.add_js_filters('select2', 'company__name')
        table.add_js_filters('totals', 'id')
        # self.add_options({
        #     'rowGroup': {'dataSrc': 'company__name',
        #                  }
        #  })
        table.table_options['ajax_url'] = self.request.path

    def add_to_context(self, **kwargs):
        context = {'description': '''
        Remove one column in mobile mode.<br>
        Filter on pk if supplied in url.
        '''}

        if 'pk' in self.kwargs:
            context['title'] = type(self).__name__ + ' ' + ' pk:' + str(self.kwargs['pk'])
        else:
            context['title'] = type(self).__name__
        return context


class CompanyView(DatatableView):
    template_name = 'table.html'

    def add_to_context(self, **kwargs):
        return {'title': type(self).__name__ + ' ' + ' pk:' + str(self.kwargs['pk'])}

    def setup_table(self, table):
        pass


class Example3(MainMenu, DatatableView):
    model = models.Company

    @staticmethod
    def badge(_column, data_dict, _page_results):
        return f'<span class="badge badge-secondary">{data_dict.get("people")}</span>'

    @staticmethod
    def range(_column, data_dict, _page_results):
        if data_dict.get('people') > 2:
            return 'GT1'
        else:
            return 'LT1'

    def setup_table(self, table):
        table.add_columns(
            'name',
            ColumnBase(column_name='CustomResultFunction', field='people', row_result=self.badge,
                       annotations={'people': Count('person__id')}, title='Send HTML'),
            ColumnBase(column_name='Range', field='people', row_result=self.range, hidden=True),
            ColumnBase(column_name='people', title='HTML generated in JS', field='people', render=[
                {'var': '%1%', 'column': 'people', 'html': '<span class="badge badge-primary">%1%</span>',
                 'function': 'Replace'},
               ]),
        )
        table.add_plugin(ColourRows, [{'column': 'Range', 'values': {'GT1': 'table-danger', 'LT1': 'table-warning'}}])
        table.sort('-people')

    def add_to_context(self, **kwargs):
        return {'description': '''
        Two different ways to add HTML to table. Using a column renderer saves on the amount of data sent to the client.
        <br>Row colours implemented with a hidden column.<br>
        Columns sorted by column_replace
        '''}


class Example4(MainMenu, DatatableView):
    model = models.Person

    @staticmethod
    def setup_table(table):
        table.edit_fields = ['first_name', 'title']
        table.add_columns(
            'id',
            'first_name',
            'date_entered',
            'title',
            'title_model',
            DateColumn('date_entered', column_name='Date'),
            'surname'
        )
        table.add_js_filters('date', 'date_entered')


class Example5(MainMenu, DatatableView):
    model = models.Company
    template_name = 'datatable_examples/example5.html'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'name',
            'Tags',
            ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
            ColumnLink(column_name='view_company_1', field=['id', 'name'], url_name='example2'),
            ColumnLink(column_name='view_company_2', link_ref_column='id', field='name', url_name='example2'),
        )
        table.add_js_filters('tag', 'Tags')


class Example6(MainMenu, DatatableView):
    model = models.Company
    template_name = 'datatable_examples/two_tables.html'

    def add_tables(self):
        self.add_table('t1', model=models.Company)
        self.add_table('t2', model=models.Person)

    @staticmethod
    def setup_t1(table):
        table.add_columns(
            'id',
            'name',
        )
        table.table_options['no_col_search'] = True

    @staticmethod
    def setup_t2(table):
        table.add_columns(
            'id',
            'first_name',
        )
    #    table.table_options.update(simple_table)


class Example7(MainMenu, DatatableView):
    model = models.Company
    template_name = 'datatable_examples/top_filter.html'
    ajax_commands = ['row']

    def row_delete(self, **kwargs):
        # Could delete from database here but for demo don't remove
        return self.command_response('delete_row', row_no=kwargs['row_no'], table_id=kwargs['table_id'])

    def row_toggle_tag(self, **kwargs):

        row_data = json.loads(kwargs['row_data'])
        table = self.tables[kwargs['table_id']]
        self.setup_tables(table_id=table.table_id)

        company = models.Company.objects.get(id=row_data[0])
        tag = models.Tags.objects.get(id=1)
        if tag in company.tags_set.all():
            company.tags_set.remove(tag)
        else:
            company.tags_set.add(tag)
        return table.refresh_row(self.request, kwargs['row_no'])

    class TagsY(DatatableColumn):

        def setup_results(self, request, all_results):
            tags = models.Tags.objects.values_list('company__id', 'id')
            tag_dict = {}
            for t in tags:
                tag_dict.setdefault(t[0], []).append(t[1])
            all_results['tags'] = tag_dict

        @staticmethod
        def proc_result(data_dict, page_results):
            return page_results['tags'].get(data_dict['id'], [])

        def col_setup(self):
            self.title = 'Tags-example'
            self.row_result = self.proc_result
            self.options['render'] = [
                {'var': '%1%', 'html': '<span class="badge badge-primary"> %1% </span>', 'function': 'ReplaceLookup'},
            ]
            self.options['lookup'] = list(models.Tags.objects.values_list('id', 'tag'))

    def setup_table(self, table):

        tags = list(models.Tags.objects.values_list('id', 'tag'))
        v_lookup = []
        for t in tags:
            if t[0] % 2:
                v_lookup.append([t[0], [t[1], 'warning']])
            else:
                v_lookup.append([t[0], [t[1], 'danger']])

        table.add_columns(
            'id',
            ColumnBase(column_name='idi', title='without helper', field=['id', 'name'], render=[
                {'var': '%1%', 'column': 'idi:0', 'html': '<b>%1%</b>&nbsp;<i>%2%</i>', 'function': 'Replace'},
                {'var': '%2%', 'column': 'idi:1', 'function': 'Replace'},
            ]),
            ColumnBase(column_name='idx', field=['id', 'name'], title='with helper', render=[
                render_replace(html='<b>%1%</b>&nbsp;<i>%2%</i>', column='idx:0'),
                render_replace(var='%2%', column='idx:1'),
            ]),
            ColumnBase(column_name='BasicButton', render=[row_button('toggle_tag', 'toggle TAG1')]),
            ColumnBase(column_name='FormattedButton', render=[row_button('toggle_tag', 'toggle TAG1',
                                                              button_classes='btn %1% btn-sm',
                                                              var='%1%',
                                                              value=1,
                                                              column='CompanyTags',
                                                              choices=['btn-success', ''],
                                                              function='ValueInColumn')]),
            ColumnBase(column_name='Delete', render=[row_button('delete', 'Delete Row')]),
            self.TagsY(column_name='tags_raw'),
            ManyToManyColumn(column_name='CompanyTags', field='tags__tag', model=models.Company,
                             html='<span class="badge badge-primary"> %1% </span>'),
            ManyToManyColumn(column_name='Coloured', field='tags__tag', model=models.Company, lookup=v_lookup,
                             render=[{'var': ['%1%', '%2%'], 'html': '<span class="badge badge-%2%"> %1% </span>',
                                      'function': 'ReplaceLookup'}]),
            ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
        )
        table.ajax_data = False
        table.add_js_filters('tag', 'CompanyTags')
        table.add_plugin(ColumnTotals, {'id': {'css_class': 'text-danger', 'text': 'Total %id%',
                                               'sum': 'to_fixed', 'decimal_places': 1},
                                        'people': {'sum': True}})


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


class Example8(MainMenu, DatatableView):
    model = models.Company

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
        # table.column('name').column_defs['orderable'] = False
        table.column('first_name').column_defs['orderable'] = False
        table.column('surname').column_defs['orderable'] = False
        table.column('collapsed').column_defs['orderable'] = False
        # table.table_options['ordering'] = False

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


class Example9(MainMenu, DatatableView):
    model = models.Company

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


class IdColumn(DatatableColumn):

    def col_setup(self):
        self.field = 'id'
        self.title = 'Class'


class Example10(MainMenu, DatatableView):
    model = models.Company

    @staticmethod
    def setup_table(table):

        table.add_columns(
            'id',                                   # string model field
            ('id', {'title': 'Tuple'}),             # tuple
            IdColumn(column_name='class_id'),       # class instance
            'ModelIdColumn',                        # column class from model
            ('ModelIdColumn', {'title': 'tuple'}),  # tuple column from model
            'model_instance',                       # column instance from model
            ('model_instance', {'title': 'tuple-instance'}),
            'person__id',                           # indirect field
            'company_list',                         # list from model
            'person__ids',                          # list from indirect model
            ('_ABC', {'render': [render_replace(column='ids/FullName', html='Full %1%')]}),
        )
        print('******************************')
        for c in table.columns:
            print((c.column_name + (' ' * 20))[:20], (str(c.field) + (' ' * 40))[:40], c.title)
        print('******************************')
        table.table_options['scrollX'] = True


class Example11(MainMenu, DatatableView):
    model = models.Company

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'test',  # parameters included in another column
            'person__c_test',   # parameters defined in model (Datatable class)
            ('person__c_test1', {'parameters': ['id', 'first_name']}),  # parameters defined in tuple

        )


class Example12(MainMenu, DatatableView):
    model = models.Company

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
        return {'description': '''
        Examples of render functions <B>Replace, ReplaceLookup, HTML</B> <br>
        also shows how lists can be accessed and displayed  
        '''}


class ExampleReorder(MainMenu, ReorderDatatableView):
    template_name = 'datatable_examples/table-nosearch.html'

    model = models.Company
    order_field = 'order'

    @staticmethod
    def setup_table(table):
        table.add_columns('name')
        table.add_plugin(Reorder)



class ExampleTotaling(MainMenu, DatatableView):
    model = models.Tally
    ajax_commands = ['row']

    @staticmethod
    def percentage(_column, data_dict, _page_results):
        number = data_dict.get(_column.field)
        if number is None:
            return ''
        else:
            number = f'{number:.1f}'
        if '.' in number:
            return number.rstrip('0').rstrip('.')
        else:
            return number

    def setup_table(self, table):
        total_vehicles_ew = ExpressionWrapper(F('cars') + F('vans'), output_field=FloatField())
        percentage_that_are_vans_ew = ExpressionWrapper(F('vans') * 100.0 / F('total_vehicles'),
                                                        output_field=FloatField())
        percentage_that_are_cars_ew = ExpressionWrapper(F('cars') * 100.0 / F('total_vehicles'),
                                                        output_field=FloatField())

        table.add_columns(
            'id',
            'cars',
            'vans',
            ColumnBase(column_name='total_vehicles',
                       field='total_vehicles',
                       annotations={'total_vehicles': total_vehicles_ew}),
            ColumnBase(column_name='percentage_that_are_vans',
                       field='percentage_that_are_vans',
                       annotations={'percentage_that_are_vans': percentage_that_are_vans_ew},
                       row_result=self.percentage,
                       render=[render_replace(html='%1%&thinsp;%', column='percentage_that_are_vans')],
                       column_defs={'className': 'dt-right'}
                       ),
            ColumnBase(column_name='percentage_that_are_cars',
                       field='percentage_that_are_cars',
                       annotations={'percentage_that_are_cars': percentage_that_are_cars_ew},
                       row_result=self.percentage,
                       render=[render_replace(html='%1%&thinsp;%', column='percentage_that_are_cars')],
                       column_defs={'className': 'dt-right'}
                       )
        )
        table.add_plugin(ColumnTotals, {'id': {'css_class': 'text-danger', 'text': 'Total'},
                                        'cars': {'sum': True},
                                        'vans': {'sum': True},
                                        'total_vehicles': {'sum': True},
                                        'percentage_that_are_vans': {'css_class': 'dt-right',
                                                                     'sum': 'percentage',
                                                                     'denominator': 'total_vehicles',
                                                                     'numerator': 'vans',
                                                                     'decimal_places': 1},
                                        'percentage_that_are_cars': {'css_class': 'dt-right',
                                                                     'sum': 'percentage',
                                                                     'denominator': 'total_vehicles',
                                                                     'numerator': 'cars',
                                                                     'decimal_places': 1}
                                        })
