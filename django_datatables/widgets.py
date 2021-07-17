from django.forms.widgets import SelectMultiple, Widget
from .datatables import DatatableTable
from .reorder_datatable import OrderedDatatable
from .columns import LambdaColumn


class DataTableWidget(SelectMultiple):

    template_name = 'datatables/widgets/datatable.html'
    crispy_kwargs = {'label_class': 'col-3 col-form-label-sm', 'field_class': 'col-12 input-group-sm'}

    tick = '<i class="fas fa-check-circle"></i>'
    no_tick = '&nbsp;'

    def __init__(self, *args, model=None, fields=None, **kwargs):
        kwargs.setdefault('attrs', {}).update({'table_model': model, 'fields': fields})
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        table = DatatableTable(context['widget']['attrs']['id'], model=self.attrs['table_model'])
        table.table_options.update(self.attrs.get('table_options', {}))
        table.table_options['pageLength'] = 400
        if 'filter' in self.attrs:
            table.filter = self.attrs['filter']
        table.add_columns(*self.attrs['fields'],  LambdaColumn(width='30px', column_name='selected', title='',
                                                               no_col_search=True, lambda_function=lambda a: '&nbsp;'))
        table.table_classes.append('multi-select')
        table.ajax_data = False
        context['tick'] = self.tick
        context['no_tick'] = self.no_tick
        context['selected_column'] = table.find_column('selected')[1]
        context['id_column'] = table.find_column('id')[1]
        context['table'] = table
        return context


class DataTableReorderWidget(Widget):
    template_name = 'datatables/widgets/datatable-reorder.html'

    crispy_kwargs = {'label_class': 'col-3 col-form-label-sm', 'field_class': 'col-12 input-group-sm'}

    def __init__(self, *args, order_field=None, model=None, fields=None, **kwargs):
        kwargs.setdefault('attrs', {}).update({'table_model': model, 'fields': fields})
        self.order_field = order_field
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        table = OrderedDatatable(context['widget']['attrs']['id'],
                                 model=self.attrs['table_model'],
                                 order_field=self.order_field)
        if 'filter' in self.attrs:
            table.filter = self.attrs['filter']
        table.add_columns(*self.attrs['fields'])
        table.ajax_data = False
        context['table'] = table
        return context
