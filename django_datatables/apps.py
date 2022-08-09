from django.apps import AppConfig
from django.conf import settings


class DjangoDatatablesConfig(AppConfig):
    name = 'django_datatables'
    default_auto_field = 'django.db.models.AutoField'
    verbose_name = 'Django datatables'

    def ready(self):
        if getattr(settings, 'DATATABLE_CACHE_SIGNAL', False) is True:
            from . import cache
            cache.setup_cache_signals()
