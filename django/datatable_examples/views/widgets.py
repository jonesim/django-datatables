from datatable_examples.views.menu import MainMenu
from datatable_examples import models
from django import forms
from django.views.generic import FormView

from django_datatables.reorder_datatable import reorder
from django_datatables.widgets import DataTableWidget, DataTableReorderWidget


class DemoForm(forms.Form):

    tags = forms.MultipleChoiceField(widget=DataTableWidget(fields=['id', 'tag'], model=models.Tags))
    order = forms.CharField(
        widget=DataTableReorderWidget(model=models.Company, order_field='order', fields=['name'])
    )


class WidgetView(MainMenu, FormView):
    template_name = 'datatable_examples/widget_example.html'
    form_class = DemoForm

    ajax_commands = ['datatable', 'button']

    def get_initial(self):
        return {'tags': [1]}

    def datatable_sort(self, **kwargs):
        form = self.get_form()
        widget = form.fields[kwargs['table_id'][3:]].widget
        reorder(widget.attrs['table_model'], widget.order_field, kwargs['sort'])
        return self.command_response('reload')