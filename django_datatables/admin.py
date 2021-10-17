from django.contrib import admin
from . import models


@admin.register(models.SavedState)
class SavedStateAdmin(admin.ModelAdmin):
    list_display = ('name', 'table_id',  'public', 'user')
