# coding=utf-8
import datatable_examples.models as models
from django.contrib import admin


@admin.register(models.TagsDirect)
class TagsDirectAdmin(admin.ModelAdmin):
    pass


class PaymentInline(admin.TabularInline):
    model = models.Payment


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    inlines = [PaymentInline]
    list_display = ['name']


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
