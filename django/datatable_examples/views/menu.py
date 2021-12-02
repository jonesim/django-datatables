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
            'example13',
            MenuItem(menu_display='Aggregations', no_hover=True,
                     dropdown=[('aggregations', 'Standard'),
                               ('aggregations_horizontal', 'Horizontal')]),
            'horizontal',
            'reorder',
            'widget',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_class'] = inspect.getmodule(self).__name__ + '.' + self.__class__.__name__
        context['title'] = type(self).__name__
        context['filter'] = filter
        return context
