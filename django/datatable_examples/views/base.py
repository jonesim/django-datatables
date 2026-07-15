from ajax_helpers.mixins import AjaxHelpers
from django_menus.menu import MenuItem, MenuMixin
from show_src_code.source_code import html_code
from show_src_code.view_mixins import DemoViewMixin

from datatable_examples.manual import CHAPTERS


class ManualPage(DemoViewMixin, AjaxHelpers, MenuMixin):
    """Base class for every page in the manual.

    Pages declare:
      page_title    - heading shown at the top of the page
      description   - via add_to_context (HTML prose explaining the feature)
      code_examples - method names (or classes/functions) whose source is
                      shown inline on the page
    """
    template_name = 'datatable_examples/table.html'
    page_title = None
    code_examples = ['setup_table']

    def setup_menu(self):
        self.add_menu('main_menu').add_items(
            MenuItem('manual_index', menu_display='Contents'),
            *[MenuItem(menu_display=chapter.title, placement='bottom-end',
                       dropdown=[MenuItem(page.url_name, menu_display=page.title) for page in chapter.pages])
              for chapter in CHAPTERS],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add_to_context (merged in DatatableView.get_context_data) may set a dynamic title
        context.setdefault('title', self.page_title if self.page_title else type(self).__name__)
        examples = [getattr(type(self), e, None) if isinstance(e, str) else e for e in self.code_examples]
        context['code_snippets'] = [html_code(e) for e in examples if e]
        return context
