from datatable_examples import models
from datatable_examples.views.menu import MainMenu
from django.views.generic import TemplateView

from django_datatables.datatables import HorizontalTable


class ExampleHorizontal(MainMenu, TemplateView):
    template_name = 'datatable_examples/horizontal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['datatable'] = HorizontalTable(model=models.Person, pk=models.Person.objects.first().id).add_columns(
            'id',
            'first_name',
            'company_id',
            'company__collink_1'
        )
        return context
