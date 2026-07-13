import io

from django.forms import CharField, Textarea
from django_modals.processes import PERMISSION_OFF

from core.modal_base import PermissionTemplateModal, PermissionModelFormModal
from file_uploads.models import FileUpload
from file_uploads.utils import get_msg_bytes


class EditFileModal(PermissionModelFormModal):
    """Set/change a file's category, revision, description and free-text notes after upload."""

    model = FileUpload
    modal_title = 'File Details'
    form_fields = ['category', 'description']
    permission_delete = PERMISSION_OFF  # deletion is done from the files table, not here

    @staticmethod
    def form_setup(form, *_args, **_kwargs):
        form.fields['description'].required = False
        meta = form.instance.metadata or {}
        # revision & notes are not columns - they live in the metadata JSONField
        form.fields['revision'] = CharField(required=False, initial=meta.get('revision', ''))
        form.fields['notes'] = CharField(required=False, widget=Textarea(attrs={'rows': 3}),
                                         initial=meta.get('notes', ''))
        return ['category', 'revision', 'description', 'notes']

    def form_valid(self, form):
        form.instance.set_extra_data('revision', form.cleaned_data.get('revision', ''))
        form.instance.set_extra_data('notes', form.cleaned_data.get('notes', ''))
        return super().form_valid(form)


class ViewFileModal(PermissionTemplateModal):

    modal_template = 'file_uploads/view_file_modal.html'
    modal_title = 'File Preview'
    size = 'xl'
    lazy = True


    def modal_context(self):
        file = FileUpload.objects.get(pk=self.slug['pk'])
        filename = (file.original_filename or '').lower()

        if filename.endswith('.msg'):
            return self._msg_context(file)

        url = file.file.url

        if filename.endswith('.pdf'):
            return {'type': 'pdf', 'url': url, 'name': file.original_filename}

        if filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            return {'type': 'image', 'url': url, 'name': file.original_filename}

        return {'type': 'other', 'name': file.original_filename}

    @staticmethod
    def _msg_context(file):
        import extract_msg

        msg = extract_msg.openMsg(io.BytesIO(get_msg_bytes(file)))

        # Read native HTML stream directly — avoids expensive RTF→HTML conversion
        # that msg.htmlBody triggers when no HTML stream is stored.
        html_body = None
        try:
            raw = msg.getStream('__substg1.0_10130102')
            if raw:
                html_body = raw.decode('utf-8', errors='replace') if isinstance(raw, bytes) else raw
        except Exception:
            pass

        attachments = []
        for i, att in enumerate(msg.attachments):
            name = getattr(att, 'longFilename', None) or getattr(att, 'shortFilename', None)
            if name:
                attachments.append((name, i))

        return {
            'type': 'msg',
            'file_pk': file.pk,
            'subject': msg.subject or '(No subject)',
            'sender': msg.sender,
            'to': msg.to,
            'cc': msg.cc,
            'date': msg.date,
            'body': msg.body,
            'html_body': html_body,
            'attachments': attachments,
        }
