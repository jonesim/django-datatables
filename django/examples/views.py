from django.db.models import Count
from django_datatables.columns import ColumnLink, ColumnReplace, ColumnBase
from django_datatables.datatables import DatatableView
from . import models
from django_datatables.filters import PivotFilter


class Example1(DatatableView):
    model = models.Company
    template_name = 'table_calcs.html'

    def setup_table(self):
        self.add_columns(
            'id',
            'name',
            'Tags',
            ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
            ColumnLink(column_name='view_company', field='name', url_name='example2'),
        )

    def add_to_context(self, **kwargs):
        self.table.pivot('people')
        # filter = PivotFilter(self.table, self.table.columns[1])

        return {'title': type(self).__name__, 'filter': filter}


class Example2(DatatableView):
    model = models.Person
    template_name = 'table.html'

    def setup_table(self):

        if self.dispatch_context['mobile']:
            self.table.omit_columns = ['first_name']

        self.add_columns(
            'id',
            'first_name',
            ('company__name', {'title': 'Company Name'}),
            'company__collink_1'
        )
        if 'pk' in self.kwargs:
            self.table.filter = {'company__id': self.kwargs['pk']}
        # self.table.pivot('company__name')
        self.table.columns[0].options['total'] = True
        self.table.columns[2].options['select2'] = True

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

    def setup_table(self):
        pass


class Example3(DatatableView):
    model = models.Company
    template_name = 'table.html'

    @staticmethod
    def badge(column, data_dict, page_results):
        return f'<span class="badge badge-secondary">{data_dict.get("people")}</span>'

    @staticmethod
    def range(column, data_dict, page_results):
        if data_dict.get('people1') > 1:
            return 'GT1'
        else:
            return 'LT1'

    def setup_table(self):
        self.add_columns(
            'name',
            ColumnBase(column_name='CustomResultFunction', field='people', row_result=self.badge,
                       annotations={'people': Count('person__id')}),
            ColumnBase(column_name='Range', field='people1', annotations={'people1': Count('person__id')},
                       row_result=self.range, hidden=True),
            ColumnReplace(column_name='ColumnReplace', field='people1',
                          replace_list=[{'column': 'ColumnReplace', 'var': '%1%'}],
                          options={'html': '<span class="badge badge-primary">%1%</span>'}))
        self.table.row_color('Range', ('GT1', 'table-danger'), ('LT1', 'table-warning'))
        self.table.sort('-ColumnReplace')

    def add_to_context(self, **kwargs):
        return {'title': type(self).__name__, 'description': '''
        Two different ways to add HMTL to table. ColumnReplace saves on the amount of data sent to the client.<br> 
        Row colours implemented with a hidden column.<br>
        Columns sorted by ColumnReplace
        '''}


class Example4(DatatableView):
    model = models.Person
    template_name = 'table.html'

    def setup_table(self):
        self.add_columns(
            'id',
            'first_name',
            'date_entered',
        )
        self.table.columns[2].options['date_filter'] = True


class Example5(DatatableView):
    model = models.Company
    template_name = 'table2.html'

    def setup_table(self):
        self.add_columns(
            'id',
            'name',
            'Tags',
            ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
            ColumnLink(column_name='view_company', field='name', url_name='example2'),
        )

    def add_to_context(self, **kwargs):
        self.table.pivot('people')
        return {'title': type(self).__name__, 'filter': filter}
