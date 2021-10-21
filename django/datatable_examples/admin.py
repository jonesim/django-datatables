# coding=utf-8
from django.contrib import admin

import datatable_examples.models as models
from django.conf import settings


@admin.register(models.TagsDirect)
class TagsDirectAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Tally)
class TallyAdmin(admin.ModelAdmin):
    list_display = ('date',
                    'cars',
                    'vans',
                    'buses',
                    'lorries',
                    'motor_bikes',
                    'push_bikes',
                    'tractors')
