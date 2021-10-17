from django.db.models import Q
from django.forms import ChoiceField
from django_modals.widgets.select2 import Select2
from django_modals.forms import CrispyForm
from django_modals.form_helpers import NoLabelsRegularHelper
from ..models import SavedState


class PickStateForm(CrispyForm):

    states = ChoiceField(label='Saved reports', choices=(('', ''),))

    def __init__(self, *args, user=None, table_id=None, **kwargs):
        kwargs['no_buttons'] = True
        super().__init__(*args, **kwargs)
        self.fields['states'].widget = Select2(attrs={'id': table_id + '_state_id'})
        reports = (SavedState.objects.order_by('name').filter(Q(public=True) | Q(user_id=user.id))
                   .values_list('id', 'name', 'public'))
        self.fields['states'].choices = [
            ('', ''),
            ('Private Reports', [(report_id, name) for report_id, name, public in reports if not public])] + [
            ('Public reports', [(report_id, name) for report_id, name, public in reports if public])]


def add_save_filters(table, user):
    table.add_js_filters('datatable_examples/save_state.html',
                         form=PickStateForm(helper_class=NoLabelsRegularHelper, user=user, table_id=table.table_id))
