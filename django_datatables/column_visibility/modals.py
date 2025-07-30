import base64

from crispy_forms.layout import HTML
from django.db import transaction
from django.forms import BooleanField
from django_modals.forms import CrispyForm
from django_modals.modals import FormModal

from django_datatables.datatables import DatatableTable
from django_datatables.models import SavedState
from django_datatables.reorder_datatable import OrderedDatatable


@transaction.atomic()
def save_table_state(user_id, table_id, view_class, name, column_order=None, column_visibility=None, state=None,
                     session_key=None):
    existing, created = SavedState.objects.get_or_create(user_id=user_id, table_id=table_id,
                                                         name=name, view_class=view_class, public=False)
    if column_order is not None:
        existing.column_order = column_order
    if column_visibility is not None:
        existing.column_visibility = column_visibility
    if state is not None:
        existing.state = state
    existing.save()


class ColumnForm(CrispyForm):

    datatable: str
    has_default: bool
    table: DatatableTable
    view_class: str

    def order_ajax(self, name):
        return {'function': 'send_column', 'column': 'col', 'table_id': self.table.table_id,
                'method': 'column_order', 'data': {'name': name}}

    def submit_button(self, *args, **kwargs):
        return self.button('Confirm', self.order_ajax('_session'), css_class=self.submit_class)

    def setup_modal(self, *args, **kwargs):
        self.buttons = [self.button('Set as Default', self.order_ajax('_default'),
                                    css_class='btn btn-primary', font_awesome='fas fa-user')]
        if self.has_default:
            self.buttons.append(self.button(
                'Remove Default', {'function': 'post_modal',
                                   'button': {'modal': 'clear_session', 'view_class': self.view_class,
                                              'table_id': self.datatable}},
                css_class='btn btn-warning', font_awesome='fas fa-user-slash'
            ))
        self.buttons += [self.submit_button(), self.cancel_button()]
        super().setup_modal(*args, **kwargs)

    def post_init(self, *args, **kwargs):
        return  [HTML(self.table.render())]

    @classmethod
    def create_from_table(cls, table, has_default):
        session = table.session_column_visibility()
        fields = {c.column_name: BooleanField(label=c.title, required=False) for c in table.columns}
        b64_key = base64.b64encode(table.session_key().encode('utf8')).decode("utf-8").rstrip('=')

        modal_table = OrderedDatatable(b64_key, order_field='order')
        modal_table.add_columns('enable', '.col', 'column', '.order')
        col_order = table.session_column_order()

        modal_table.table_data = []

        for c, column in enumerate(table.columns):
            if column.options.get('hidden'):
                continue
            order = (col_order.get(column.column_name)
                     if col_order and col_order.get(column.column_name) else c)
            modal_table.table_data.append({
                'index': order,
                'pk': column.column_name,
                'handle': '<i class="btn btn-sm btn-outline-secondary fas fa-arrows-alt-v"></i>',
                'order': order,
                'column': column.title,
                'col': column.column_name,
                'enable': str(BooleanField().widget.render(name=column.column_name, value=session.get(
                    column.column_name) if session else not column.optional))
            })
        new_form = type('ColumnForm', (cls,), dict(
            datatable=table.table_id, initial=table.session_column_visibility, table=modal_table,
            has_default=has_default, view_class=table.view.__class__.__name__, **fields
        ))
        return new_form


class DatatableColumnModal(FormModal):
    form_class = None
    focus = False
    modal_title = 'Select Columns'

    def dispatch(self, request, *args, **kwargs):
        self.form_class = kwargs['form_class']
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        save_table_state(user_id=self.request.user.id,
                         name=self.request.POST['name'],
                         table_id=self.request.POST['datatable'],
                         view_class=self.request.POST['view_class'],
                         column_visibility=form.cleaned_data,
                         session_key= self.request.session.session_key)
        return super().form_valid(form)


