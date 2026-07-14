from django.db import models
from django.conf import settings


class SavedState(models.Model):
    table_id = models.CharField(max_length=80)
    view_class = models.CharField(max_length=80, blank=True, null=True)
    column_order = models.JSONField(default=dict, blank=True, null=True)
    column_visibility = models.JSONField(default=dict, blank=True, null=True)
    state = models.CharField(max_length=32768, blank=True, null=True)
    name = models.CharField(max_length=80)
    public = models.BooleanField(verbose_name='Public/Private', default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['table_id', 'view_class', 'name', 'user']

    def __str__(self):
        return self.name
