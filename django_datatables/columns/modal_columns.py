"""Columns that link to django-modals dialogs.

These are kept in their own module (rather than in ``columns.columns``) so that importing the
columns package does not require django-modals unless these columns are actually used.
"""
from django_modals.helper import show_modal

from django_datatables.columns.column_base import ColumnBase
from django_datatables.columns.columns import DatatableColumn
from django_datatables.helpers import render_replace, extract_fields


class ModalLink(ColumnBase):
    """Render the cell as a link (or button) that opens a django-modals modal for the row."""

    def __init__(self, *, modal_name=None, field='id', row_modify=False, base64=False, button_text=None, modal_args=(),
                 css_class=None, row=False, **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        if not modal_name:
            modal_name = self.model.modal_name

        modal_kwargs = {}
        if row_modify:
            modal_kwargs['row'] = True
        modal_call = show_modal(modal_name, *modal_args, datatable=True, base64=base64, href=True, **modal_kwargs)
        css_class = f' class="{css_class}"' if css_class is not None else ""
        link = f'<a href="{modal_call}"{css_class}>{{}}</a>'

        if button_text:
            self.options['render'] = [
                render_replace(column=self.column_name, html=link.format(button_text), var='%ref%', row=row),
            ]
            self.column_defs = {
                'orderable': False,
                'className': 'dt-center'
            }
        else:
            self.options['render'] = [
                render_replace(column=f'{self.column_name}:0', html=link.format('%1%'), var='%ref%', row=row),
                render_replace(column=f'{self.column_name}:1')
            ]

        if row_modify:
            self.options['render'].append({'function': 'Row', 'var': '%row%'})

    @staticmethod
    def excel(value):
        if isinstance(value, list):
            return value[0]


class ColumnLinkCoalesce(DatatableColumn):
    """Modal link whose display text is the first non-null of several ``display_fields``."""

    base_link_html = '%1%'
    base_link_css = None

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url_name):
        self._url = show_modal(url_name, datatable=True, href=True)

    @extract_fields
    def row_result(self, _data_dict, _page_results, fields):
        for f in fields[1:]:
            if f is not None:
                return [fields[0], f]
        return [fields[0], None]

    # noinspection PyAttributeOutsideInit
    def col_setup(self):
        if 'link_ref_column' in self.kwargs:
            link_ref_column = self.model_path + self.kwargs['link_ref_column']
        else:
            link_ref_column = self.column_name

        self.url = self.kwargs.get('url_name')
        link_html = self.kwargs.get('link_html', self.base_link_html)
        link_css = self.kwargs.get('link_css', self.base_link_css)
        self.var = self.kwargs.get('var', '%1%')
        self.link_ref_column = link_ref_column
        self.field = [self.field] + self.kwargs['display_fields']
        link_css = f' class="{link_css}"' if link_css else ''
        link = f'<a{link_css} href="{self.url}">{{}}</a>'
        self.options['render'] = [
            render_replace(column=self.column_name + ':0', html=link.format(link_html), var='%ref%'),
            render_replace(column=self.column_name + ':1'),
        ]


modal_row_js = ("(function(b){var r=$(b).closest('tr').attr('id');"
                "django_modal.process_commands_lock("
                "[{function:'post_modal', button:{row:$(b).attr('data-command'),row_no:r}}])})(this)")


def modal_row_button(command, button_text, button_classes='btn btn-sm', function='Html'):
    """Render a button that triggers a row_* method on a modal that hosts a datatable.

    Use the standard pattern - ``DatatableColumn(render=modal_row_button(command, text))``.
    """
    return {'html': (f'<button data-command="{command}" onclick="{modal_row_js}" '
                     f'class="{button_classes}" type="button">{button_text}</button>'),
            'function': function}
