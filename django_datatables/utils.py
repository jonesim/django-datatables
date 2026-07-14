from django.core.cache import cache


def get_msg_bytes(file):
    key = f'msg_bytes_{file.pk}'
    data = cache.get(key)
    if data is None:
        with file.file.open('rb') as f:
            data = f.read()
        cache.set(key, data, timeout=60)
    return data
