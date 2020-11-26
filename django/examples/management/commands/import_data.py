import csv
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from examples import models


class Command(BaseCommand):
    def handle(self, *args, **options):

        with open(str(settings.BASE_DIR) + '/test_data.csv', 'r') as f:
            csv_reader = csv.DictReader(f)
            for r in csv_reader:

                companies = models.Company.objects.filter(name=r['Company'])
                if len(companies) > 1:
                    for c in companies[1:]:
                        c.delete()

                company = models.Company.objects.get_or_create(name=r['Company'])[0]
                models.Person.objects.get_or_create(company=company,
                                                    first_name=r['First Name'],
                                                    surname=r['Surname'],
                                                    date_entered=datetime.datetime.strptime(r['date_entered'],
                                                                                            '%d/%m/%Y'))
                for tag in r['tags'].split(','):
                    if tag!='':
                        tag = models.Tags.objects.get_or_create(tag=tag)[0]
                        tag.company.add(company)
