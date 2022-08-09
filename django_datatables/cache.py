import json

# noinspection PyPackageRequirements
import redis
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, m2m_changed


def setup_cache_signals():
    post_save.connect(invalidate_caches)
    m2m_changed.connect(invalidate_caches)


def cancel_cache_signals():
    post_save.disconnect(invalidate_caches)
    m2m_changed.disconnect(invalidate_caches)


# noinspection PyUnusedLocal
def invalidate_caches(sender, instance, **_kwargs):
    sender_model = ContentType.objects.get_for_model(sender)
    apps = getattr(settings, 'DATATABLE_SIGNAL_APPS', None)
    model_name = f'{sender_model.app_label}.{sender_model.model}'
    if apps is None or sender_model.app_label in apps:
        included_models = getattr(settings, 'DATATABLE_SIGNAL_MODELS', None)
        if included_models is None or model_name in included_models:
            redis_instance = DataTableCache.get_redis_instance()
            try:
                stored_tables = redis_instance.smembers(DataTableCache.cached_tables)
                if stored_tables:
                    for st in stored_tables:
                        table_data = json.loads(st)
                        try:
                            if model_name in table_data['models']:
                                redis_instance.delete(table_data['key'])
                                redis_instance.srem(DataTableCache.cached_tables, st)
                        except KeyError:
                            redis_instance.srem(DataTableCache.cached_tables, st)
            except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError):
                return


class DataTableCache:
    cached_tables = 'stored_tables'

    def __init__(self):
        self.redis_instance = self.get_redis_instance()

    @staticmethod
    def get_redis_instance():
        return redis.StrictRedis(host=getattr(settings, 'REDIS_HOST', 'redis'),
                                 socket_timeout=getattr(settings, 'REDIS_TIMEOUT', 1))

    def get_cache(self, table):
        try:
            return self.redis_instance.get(table.table_id)
        except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError):
            return

    def store_cache(self, table, data):
        try:
            self.redis_instance.sadd(self.cached_tables, json.dumps(
                {'key': table.table_id,
                 'models': getattr(table, 'cached_linked_tables', [])}
            ))
            self.redis_instance.set(table.table_id, data, ex=table.cache_expiry)
        except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError):
            return
