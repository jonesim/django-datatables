from django.db.models import Count
from django.views.generic import TemplateView
from django_menus.menu import MenuItem

from datatable_examples import models
from datatable_examples.manual import CHAPTERS
from datatable_examples.views.base import ManualPage
from django_datatables.columns import ColumnBase, DatatableColumn
from django_datatables.datatables import DatatableView
from django_datatables.helpers import render_replace


class ManualIndex(ManualPage, TemplateView):
    template_name = 'datatable_examples/index.html'
    page_title = 'Contents'

    def setup_menu(self):
        super().setup_menu()
        for no, chapter in enumerate(CHAPTERS):
            self.add_menu(f'chapter_{no}', 'buttons',
                          button_defaults={'css_classes': 'btn-link text-left d-block p-0'}).add_items(
                *[MenuItem(page.url_name, menu_display=page.title) for page in chapter.pages]
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chapters'] = [{'title': chapter.title, 'menu': self.menus[f'chapter_{no}']}
                               for no, chapter in enumerate(CHAPTERS)]
        context['description'] = (
            'A tour of <b>django-datatables</b> (PyPI: <code>django-filtered-datatables</code>) — '
            'server-backed DataTables.js tables for Django with filtering, sorting, inline editing, '
            'state persistence and Excel export. Every page demonstrates one feature with a live table, '
            'an explanation, the key code inline, and the full view source behind the '
            '<i>Source Code</i> button.'
        )
        return context


class FirstTable(ManualPage, DatatableView):
    model = models.Company
    page_title = 'A First Table'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'name',
            ColumnBase(column_name='people', field='people', annotations={'people': Count('person__id')}),
        )

    def add_to_context(self, **kwargs):
        return {'description': (
            'The smallest useful datatable. A view extends <code>DatatableView</code>, sets '
            '<code>model</code>, and adds columns in <code>setup_table</code>. GET renders the page; '
            'the table data is requested by DataTables.js with a POST to the same URL. '
            'Columns can be plain model field names (including <code>related__field</code> paths) or '
            'column objects — here <code>ColumnBase</code> with an <code>annotations</code> dict adds '
            'a calculated column counting each company\'s people.'
        )}


class IdColumn(DatatableColumn):

    def col_setup(self):
        self.field = 'id'
        self.title = 'Class'


class ColumnDefinitions(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Ways to Define Columns'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',                                   # string model field
            ('id', {'title': 'Tuple'}),             # tuple
            IdColumn(column_name='class_id'),       # class instance
            'ModelIdColumn',                        # column class from model
            ('ModelIdColumn', {'title': 'tuple'}),  # tuple column from model
            'model_instance',                       # column instance from model
            ('model_instance', {'title': 'Instance via tuple'}),
            'person__id',                           # indirect field
            'company_list',                         # list from model
            'person__ids',                          # list from indirect model
            ('_full_name', {'render': [render_replace(column='ids/FullName', html='Full %1%')]}),
        )
        table.table_options['scrollX'] = True

    def add_to_context(self, **kwargs):
        return {'description': (
            'Every way a column can be declared in <code>add_columns</code>: a model field name, '
            'a <code>(name, kwargs)</code> tuple, a <code>DatatableColumn</code> subclass or instance, '
            'a column declared on the model\'s inner <code>Datatable</code> class (optionally reached '
            'through a foreign key with <code>related__column</code>), and a list of columns defined '
            'on the model. A leading underscore creates an unbound column that is filled by a render '
            'function.'
        )}


class ColumnParameters(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Column Parameters'

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'id_label',  # parameters included in another column
            'person__id_and_title',   # parameters defined in model (Datatable class)
            ('person__id_and_first_name', {'parameters': ['id', 'first_name']}),  # parameters defined in tuple
        )

    def add_to_context(self, **kwargs):
        return {'description': (
            'Columns whose value comes from calling a model method. The fields the method needs are '
            'declared as <code>parameters</code> — either on the model\'s inner <code>Datatable</code> '
            'class or in the column tuple — so the query fetches them and the method is called on a '
            'reconstructed object for each row.'
        )}
