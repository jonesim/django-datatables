import csv
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from datatable_examples import models


class Command(BaseCommand):
    def handle(self, *args, **options):
        if models.Company.objects.exists():
            self.stdout.write('Data already imported, skipping.')
            return
        self.import_companies()
        self.import_tallies()
        self.import_payments()

    @staticmethod
    def import_companies():

        with open(str(settings.BASE_DIR) + '/test_data.csv', 'r') as f:

            titles = {c[1]: c[0] for c in models.Person.title_choices}
            csv_reader = csv.DictReader(f)
            for r in csv_reader:

                companies = models.Company.objects.filter(name=r['Company'])
                if len(companies) > 1:
                    for c in companies[1:]:
                        c.delete()

                company = models.Company.objects.get_or_create(name=r['Company'])[0]
                person = models.Person.objects.get_or_create(company=company,
                                                             first_name=r['First Name'],
                                                             surname=r['Surname'],
                                                             title=titles.get(r['Title'], None),
                                                             date_entered=datetime.datetime.strptime(r['date_entered'],
                                                                                                     '%d/%m/%Y'))[0]
                # Deterministic JSON options for the server-side JSON column
                # example; every third person has no key at all.
                options = {} if person.id % 3 == 0 else {'newsletter': person.id % 2 == 0}
                if person.options != options:
                    person.options = options
                    person.save()
                for tag in r['tags'].split(','):
                    if tag != '':
                        tag = models.Tags.objects.get_or_create(tag=tag)[0]
                        tag.company.add(company)

    @staticmethod
    def import_payments():
        # Deterministic payments derived from the company id so reruns are
        # idempotent; every fifth company gets none.
        for company in models.Company.objects.all():
            if company.id % 5 == 0:
                continue
            for i in range(company.id % 4 + 1):
                models.Payment.objects.get_or_create(
                    company=company,
                    date=datetime.date(2023, i % 12 + 1, company.id % 28 + 1),
                    amount=(company.id * 37 + i * 130) % 2000 + 50,
                    quantity=i + 1,
                )

    @staticmethod
    def import_tallies():
        with open(str(settings.BASE_DIR) + '/test_tallies_data.csv', 'r') as f:
            csv_reader = csv.DictReader(f)
            for r in csv_reader:
                models.Tally.objects.get_or_create(date=datetime.datetime.strptime(r['Date'], '%d/%m/%Y'),
                                                   cars=int(r['Cars']),
                                                   vans=int(r['Vans']),
                                                   buses=int(r['Buses']),
                                                   lorries=int(r['Lorries']),
                                                   motor_bikes=int(r['Motor Bikes']),
                                                   push_bikes=int(r['Push Bikes']),
                                                   tractors=int(r['Tractors']))
