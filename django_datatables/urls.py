from django.urls import path
from .modals import SaveStateModal

app_name = 'django_datatables'

urlpatterns = [
    path('save_state/<slug:slug>/', SaveStateModal.as_view(), name='save_state'),
]
