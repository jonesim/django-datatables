from django.db import models
from django.db.models import Count
from django_datatables.model_def import DatatableModel
from django_datatables.columns import ColumnLink, DatatableColumn


class Company(models.Model):
    name = models.CharField(max_length=80)

    class Datatable(DatatableModel):
        people = {'annotations': {'people': Count('person__id')}}
        collink_1 = ColumnLink(title='Defined in Model', field='name', url_name='company')

        class Tags(DatatableColumn):
            def setup_results(self, request, all_results):
                tags = Tags.objects.values_list('company__id', 'id')
                tag_dict = {}
                for t in tags:
                    tag_dict.setdefault(t[0], []).append(t[1])
                all_results['tags'] = tag_dict

            def proc_result(self, data_dict, page_results):
                return page_results['tags'][data_dict['id']]

            def col_setup(self):
                self.options['lookup'] = list(Tags.objects.values_list('id', 'tag'))
                self.options['renderfn'] = 'lookupRender'
                self.row_result = self.proc_result


class Person(models.Model):
    company = models.ForeignKey(Company,  on_delete=models.CASCADE)
    first_name = models.CharField(max_length=80)
    surname = models.CharField(max_length=80)
    date_entered = models.DateField()


class Tags(models.Model):
    tag = models.CharField(max_length=40)
    company = models.ManyToManyField(Company)

