import inspect

from ajax_helpers.mixins import AjaxHelpers
from django_menus.menu import MenuMixin, MenuItem
from show_src_code.view_mixins import DemoViewMixin


class MainMenu(DemoViewMixin, AjaxHelpers, MenuMixin):
    template_name = 'datatable_examples/table.html'

    def setup_menu(self):

        self.add_menu('main_menu').add_items(
            'example1',
            'example2',
            'example3',
            'example4',
            'example5',
            'example6',
            'example7',
            'example8',
            'example9',
            'example10',
            'example11',
            'example12',
            MenuItem(menu_display='No model', placement='bottom-end',
                     dropdown=[MenuItem('no_model_ajax_version', menu_display='AJAX version'),
                               MenuItem('no_model_non_ajax_version', menu_display='Non AJAX version')]),
            MenuItem(menu_display='Aggregations', no_hover=True,
                     dropdown=[('aggregations', 'Standard'),
                               ('aggregations_horizontal', 'Horizontal')]),
            'horizontal',
            'reorder',
            'widget',
            'selection_example',
            'modal_filter',
            'spreadsheet',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_class'] = inspect.getmodule(self).__name__ + '.' + self.__class__.__name__
        context['title'] = type(self).__name__
        context['filter'] = filter
        return context
