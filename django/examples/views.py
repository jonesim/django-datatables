import csv
from django.db.models import Count
from django_datatables.columns import ColumnLink, ColumnBase, DatatableColumn, row_button, render_replace, \
    ManyToManyColumn, DateColumn
from django_datatables.datatables import DatatableView, simple_table, row_link
from django.http import HttpResponse
from . import models
from django_datatables.colour_rows import ColourRows


#        table.table_options.update({'rowGroup': {'dataSrc': 'name'}})

class Example1(DatatableView):
    model = models.Company
    template_name = 'table.html'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            ('id', {'column_defs': {'width': '30px'}}),
            'name',
            'Tags',
            ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
            ColumnLink(column_name='view_company', field='name', url_name='example2'),
            ColumnLink(column_name='view_company_icon', link_ref_column='id', url_name='example2', width='10px',
                       link_html='<button class="btn btn-sm btn-outline-dark"><i class="fas fa-building"></i></button>'
                       ),
            'reverse_tag',
            ManyToManyColumn(column_name='DirectTag', field='direct_tag__tag_direct', model=models.Company,
                             html='<span class="badge badge-primary"> %1% </span>'),
        )
        table.column('name').column_defs['orderable'] = False
        table.add_plugin(ColourRows, [{'column': 0, 'values': {'1': 'table-danger'}}])
        table.ajax_data = False
        table.add_js_filters('tag', 'Tags')
        table.add_js_filters('totals', 'people', filter_title='Number of People', collapsed=False)

        table.table_options['row_href'] = row_link('example2', 'id')
        # table.table_options['row_href'] = [render_replace(column='id', html='javascript:console.log("%1%")')]

    def add_to_context(self, **kwargs):
        return {'title': type(self).__name__, 'filter': filter}


class Example2(DatatableView):
    model = models.Person
    template_name = 'table2.html'

    @staticmethod
    def column_get_csv(request, column_values, table, _extra_data):

        # Does not filter out hidden columns but can easily be modified

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="test.csv"'
        table.filter['id__in'] = column_values
        results = table.get_table_array(request, table.get_query())
        writer = csv.writer(response)
        writer.writerow(table.all_titles())
        for r in results:
            writer.writerow(r)
        return response

    def setup_table(self, table):

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


class Example3(DatatableView):
    model = models.Company
    template_name = 'table.html'

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
        table.row_color('Range', ('GT1', 'table-danger'), ('LT1', 'table-warning'))
        table.sort('-people')

    def add_to_context(self, **kwargs):
        return {'title': type(self).__name__, 'description': '''
        Two different ways to add HMTL to table. Using a column renderer saves on the amount of data sent to the client.
        <br>Row colours implemented with a hidden column.<br>
        Columns sorted by column_replace
        '''}


class Example4(DatatableView):
    model = models.Person
    template_name = 'table.html'

    @staticmethod
    def setup_table(table):
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


class Example5(DatatableView):
    model = models.Company
    template_name = 'table5.html'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'name',
            'Tags',
            ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
            ColumnLink(column_name='view_company', field='name', url_name='example2'),
        )
        table.add_js_filters('tag', 'Tags')

    def add_to_context(self, **kwargs):
        return {'title': type(self).__name__, 'filter': filter}


class Example6(DatatableView):
    model = models.Company
    template_name = 'table6.html'

    def add_tables(self):
        self.add_table('t1', model=models.Company)
        self.add_table('t2', model=models.Person)

    @staticmethod
    def setup_t1(table):
        table.add_columns(
            'id',
            'name',
        )

    @staticmethod
    def setup_t2(table):
        table.add_columns(
            'id',
            'first_name',
        )
        table.table_options.update(simple_table)

    def add_to_context(self, **kwargs):
        return {'title': type(self).__name__, 'filter': filter}


class Example7(DatatableView):
    model = models.Company
    template_name = 'table7.html'

    @staticmethod
    def row_delete(request, _row, table, extra_data):
        # Could delete from database here but for demo don't remove
        return table.delete_row(request, extra_data['row_no'])

    @staticmethod
    def row_toggle_tag(request, row, table, extra_data):
        company = models.Company.objects.get(id=row[0])
        tag = models.Tags.objects.get(id=1)
        if tag in company.tags_set.all():
            company.tags_set.remove(tag)
        else:
            company.tags_set.add(tag)
        return table.refresh_row(request, extra_data['row_no'])

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
            ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
        )
        table.ajax_data = False
        table.add_js_filters('tag', 'CompanyTags')

    def add_to_context(self, **kwargs):
        return {'title': type(self).__name__, 'filter': filter}


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


class Example8(DatatableView):
    model = models.Company
    template_name = 'table.html'

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

    def add_to_context(self, **kwargs):
        return {'title': type(self).__name__, 'filter': filter}

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


class Example9(DatatableView):
    model = models.Company
    template_name = 'table.html'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            ('id', {'column_defs': {'width': '30px'}}),
            'name',
            ColumnBase(column_name='title', field='person__title',
                       choices=dict(models.Person._meta.get_field('title').choices),
                       render=[render_replace(html='ABC -%1%- DFG', column='title')]),
            ColumnBase(column_name='Title', field=['person__title', 'person__first_name'],
                       render=[{'function': 'Replace', 'html': '%1%  - %2%  -  %1%',
                                'column': 'Title:0', 'null_value': 'x',   'var': '%1%'},
                               {'function': 'Replace', 'column': 'Title:1',  'var': '%2%'}]),
        )
        table.table_options['row_href'] = [render_replace(column='id', html='javascript:console.log("%1%")')]

    def add_to_context(self, **kwargs):
        return {'title': type(self).__name__, 'filter': filter}
