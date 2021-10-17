from django.utils.safestring import mark_safe
from crispy_forms.bootstrap import StrictButton
from django_modals.modals import ModelFormModal
from django_modals.widgets.widgets import Toggle
from .models import SavedState

from django_modals.processes import PROCESS_DELETE, PERMISSION_METHOD, PROCESS_EDIT_DELETE


class SaveStateModal(ModelFormModal):
    model = SavedState
    form_fields = ['name', ('public', {'widget': Toggle(attrs={'data-on': 'Public', 'data-off': 'Private'})})]

    permission_delete = PERMISSION_METHOD

    def permission(self, user, process):
        if process in [PROCESS_EDIT_DELETE, PROCESS_DELETE] and user != self.object.user and not user.is_superuser:
            return False
        return True

    @staticmethod
    def form_setup(form, **_kwargs):
        form.buttons = [StrictButton(
            'Submit',
            onclick=mark_safe(
                ("django_modal.process_commands_lock([{'function': 'post_modal', button: {state: datatable_state('" +
                 form.instance.table_id + "')}}])")),
            css_class=form.submit_class),
            ]
        if form.process == 4:
            form.buttons.append(form.delete_button())

        form.buttons.append(form.cancel_button())

    def form_valid(self, form):
        if not self.object.user and not self.request.user.is_anonymous:
            self.object.user = self.request.user
        self.object.state = self.request.POST['state']
        return super().form_valid(form)
