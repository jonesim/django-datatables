from django.urls import path
from .modals import SaveStateModal

urlpatterns = [
    path('/save_state/<slug:slug>/', SaveStateModal.as_view(), name='datatable_save_state'),
]
