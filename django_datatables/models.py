from django.db import models
from django.conf import settings


class SavedState(models.Model):
    table_id = models.CharField(max_length=80)
    state = models.CharField(max_length=8192)
    name = models.CharField(max_length=80)
    public = models.BooleanField(verbose_name='Public/Private')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name
