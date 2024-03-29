from django.db import models
from django.db.models import Count
from django_datatables.model_def import DatatableModel
from django_datatables.columns import ColumnLink, DatatableColumn, ChoiceColumn, ManyToManyColumn, render_replace


class TagsDirect(models.Model):
    tag_direct = models.CharField(max_length=40)

    def __str__(self):
        return self.tag_direct


class Company(models.Model):
    name = models.CharField(max_length=80)
    direct_tag = models.ManyToManyField(TagsDirect, blank=True)
    dissolved = models.BooleanField(default=False)
    order = models.IntegerField(null=True)

    def test(self):
        return f' test - {self.id}'

    class Datatable(DatatableModel):
        people = {'annotations': {'people': Count('person__id')}}
        collink_1 = ColumnLink(title='Defined in Model', field=['id', 'name'], url_name='example2')
        company_list = ['id', 'name']

        class ModelIdColumn(DatatableColumn):
            def col_setup(self):
                self.field = 'id'
                if 'title' not in self.kwargs:
                    self.title = 'Modal Class'
        model_instance = ModelIdColumn(title='Instance')
        direct_tag = ManyToManyColumn(field='direct_tag__tag_direct')
        reverse_tag = ManyToManyColumn(field='tags__tag')

        class Tags(DatatableColumn):
            def setup_results(self, request, all_results):
                tags = Tags.objects.values_list('company__id', 'id')
                tag_dict = {}
                for t in tags:
                    tag_dict.setdefault(t[0], []).append(t[1])
                all_results['tags'] = tag_dict

            @staticmethod
            def proc_result(data_dict, page_results):
                return page_results['tags'].get(data_dict['id'], [])

            def col_setup(self):
                self.options['render'] = [
                    {'var': '%1%', 'html': '%1%', 'function': 'ReplaceLookup'},
                ]
                self.options['lookup'] = list(Tags.objects.values_list('id', 'tag'))
                self.row_result = self.proc_result


class Person(models.Model):

    class Datatable(DatatableModel):
        c_test = {'parameters': ['id', 'title']}

        class FullName(DatatableColumn):

            def row_result(self, data_dict, _page_result):
                return f'{data_dict[self.field[0]]} - {data_dict[self.field[1]]}'

            def col_setup(self):
                self.field = ['first_name', 'surname']

        title_model = ChoiceColumn('title', choices=((0, 'Mr'), (1, 'Mrs'), (2, 'Miss')))
        ids = [
            'title',
            ('id', {'render': [render_replace(column='ids/id', html='render %1%')]}),
            FullName,
        ]

    def c_test(self):
        return f'{self.id} - {self.title}'

    def c_test1(self):
        return f'{self.id} - {self.first_name}'

    title_choices = ((0, 'Mr'), (1, 'Mrs'), (2, 'Miss'))
    title = models.IntegerField(choices=title_choices, null=True)
    company = models.ForeignKey(Company,  on_delete=models.CASCADE)
    first_name = models.CharField(max_length=80)
    surname = models.CharField(max_length=80)
    date_entered = models.DateField()


class Tags(models.Model):
    tag = models.CharField(max_length=40)
    company = models.ManyToManyField(Company)

    def __str__(self):
        return self.tag


class Tally(models.Model):
    date = models.DateField()
    cars = models.IntegerField()
    vans = models.IntegerField()
    buses = models.IntegerField()
    lorries = models.IntegerField()
    motor_bikes = models.IntegerField()
    push_bikes = models.IntegerField()
    tractors = models.IntegerField()

    class Meta:
        verbose_name_plural = 'Tallies'


class Payment(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.IntegerField()
    quantity = models.IntegerField(default=1)
