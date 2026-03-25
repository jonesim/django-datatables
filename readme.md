[![PyPI version](https://badge.fury.io/py/django-filtered-datatables.svg)](https://badge.fury.io/py/django-filtered-datatables)

# django-filtered-datatables

A Django library for building interactive data tables powered by [DataTables.js](https://datatables.net/), with server-side processing, dynamic JavaScript filters, inline editing, and a rich plugin system.

Define your tables in Python using Django models and ORM queries -- columns, filters, sorting, annotations, and rendering are all configured from your views, with minimal JavaScript required.

## Features

- **20+ column types** -- dates, currency, booleans, links, many-to-many, choice fields, lambdas, and more
- **AJAX and non-AJAX modes** -- load data dynamically or render inline
- **JavaScript filters** -- pivot, tag, select2, date range, and text search filters
- **Modal filter dialogs** -- form-based filtering with crispy-forms support
- **Inline editing** -- edit cells directly in the table with select2 dropdowns or text inputs
- **Row selection** -- checkbox-based row selection with bulk actions
- **Plugins** -- column totals, conditional row colouring, drag-and-drop reordering, save/restore filter state
- **Data export** -- Excel (.xlsx) download and clipboard copy
- **Client-side rendering** -- render functions for badges, links, conditional formatting, and lookups
- **Django ORM integration** -- annotations, aggregations, foreign key traversal, callable model methods
- **Model-defined columns** -- configure columns directly on your Django models via an inner `Datatable` class
- **Multiple tables per view** -- display several tables on a single page
- **Spreadsheet mode** -- JSpreadsheet integration for spreadsheet-like editing
- **Form widgets** -- `DataTableWidget` and `DataTableReorderWidget` for use in Django forms
- **Mobile responsive** -- automatic device detection with per-device column visibility
- **Redis caching** -- optional cache layer with signal-based invalidation

## Installation

```bash
pip install django-filtered-datatables
```

Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'django_datatables',
    'ajax_helpers',
    # ...
]
```

Include the required JavaScript and CSS in your base template. The library depends on DataTables.js, jQuery, and Bootstrap.

## Quick Start

### 1. Define a view

```python
from django_datatables.datatables import DatatableView

class CompanyList(DatatableView):
    model = Company

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            'name',
            'dissolved',
        )
```

### 2. Wire up the URL

```python
urlpatterns = [
    path('companies/', CompanyList.as_view(), name='company-list'),
]
```

### 3. Use the template

The default template renders a complete DataTables table. You can override it via `template_name` on your view.

## Usage

### Adding Columns

Columns can be added in several ways:

```python
def setup_table(table):
    table.add_columns(
        'name',                                          # model field name
        ('id', {'title': 'ID', 'width': '30px'}),       # tuple with options
        DateColumn('date_entered', column_name='Date'),  # column class instance
        'company__name',                                 # foreign key traversal
        'Tags',                                          # model-defined column
    )
```

**String prefix syntax** for quick column options:
- `.field` -- hidden column (still available for filtering/rendering)
- `_field` -- calculated column (not from the database)
- `$field` -- secure column (hidden from client source)

### Column Types

| Column | Purpose |
|--------|---------|
| `DatatableColumn` | Standard column with customisable `row_result` and `col_setup` |
| `DateColumn` | Formats dates (dd/mm/yyyy) |
| `DateTimeColumn` | Formats datetimes |
| `ChoiceColumn` | Maps integer choices to display labels |
| `CurrencyColumn` | Currency formatting |
| `BooleanColumn` | Boolean display |
| `ColumnLink` | Clickable link using Django URL names |
| `ManyToManyColumn` | Displays many-to-many relationships |
| `CallableColumn` | Calls a model method |
| `LambdaColumn` | Processes values with a lambda function |
| `SelectColumn` | Row selection checkboxes |
| `TextFieldColumn` | Long text with truncation |

### Model-Defined Columns

Configure columns directly on your models:

```python
class Company(models.Model):
    name = models.CharField(max_length=80)

    class Datatable(DatatableModel):
        # Annotation-based column
        people = {'annotations': {'people': Count('person__id')}}

        # Link column
        collink_1 = ColumnLink(title='View', field=['id', 'name'], url_name='company-detail')

        # Column list (renders multiple fields as a group)
        company_list = ['id', 'name']

        # Custom column class
        class ModelIdColumn(DatatableColumn):
            def col_setup(self):
                self.field = 'id'
                self.title = 'Custom ID'
```

These columns can then be referenced by name in `add_columns()`:

```python
table.add_columns('id', 'name', 'people', 'collink_1', 'ModelIdColumn')
```

### Filters

```python
def setup_table(table):
    table.add_columns('id', 'name', 'company__name', 'Tags')

    # JavaScript filters
    table.add_js_filters('tag', 'Tags')                    # tag filter
    table.add_js_filters('select2', 'company__name')       # select2 dropdown
    table.add_js_filters('totals', 'id')                   # totals/count filter
    table.add_js_filters('date', 'date_entered')           # date range
    table.add_js_filters('expand', 'level', id_column='id')  # tree expand

    # ORM-level filters
    table.filter = {'company__id': 1}
    table.exclude = {'dissolved': True}
```

#### Modal Filter (form-based)

```python
from django_datatables.modal_filter.mixins import DatatableFilterMixin, DatatableFilterField

class CompanyList(DatatableFilterMixin, DatatableView):
    model = Company
    filter_fields = [
        DatatableFilterField('Company Name', CharField(required=False), datatable_field='name__contains'),
        DatatableFilterField('Tags', FilterModelMultipleChoiceField(queryset=Tags.objects.all()), datatable_field='tags__in'),
    ]
```

### Sorting

```python
table.sort('name')           # ascending
table.sort('-name')          # descending
table.sort('name', '-id')   # multi-column
```

### Column Search

Per-column search boxes appear below the header by default. Customise them:

```python
table.add_columns(
    ColumnBase(column_name='status', field='dissolved',
               col_search_select=[['true', 'Dissolved'], ['false', 'Active']]),
    ColumnBase(column_name='order', field='order', no_col_search=True),
)
table.table_options['no_col_search'] = True  # disable all column search
```

### Client-Side Rendering

Render functions transform cell data in the browser without extra server round-trips:

```python
from django_datatables.helpers import render_replace, row_button

table.add_columns(
    # Badge rendering
    ColumnBase(column_name='people', field='people', render=[
        render_replace(column='people', html='<span class="badge badge-primary">%1%</span>'),
    ]),

    # Row action button
    ColumnBase(column_name='action', render=[row_button('delete', 'Delete')]),

    # Lookup-based rendering
    ('id', {'title': 'Status', 'render': [
        {'function': 'ReplaceLookup', 'html': '%1%', 'var': '%1%'}
    ], 'lookup': [[1, 'Active'], [2, 'Inactive']]}),
)
```

Available render functions: `Replace`, `ReplaceLookup`, `Html`, `MergeArray`, `ValueInColumn`.

### Plugins

```python
from django_datatables.plugins.colour_rows import ColourRows
from django_datatables.plugins.column_totals import ColumnTotals
from django_datatables.plugins.reorder import Reorder

# Conditional row colouring
table.add_plugin(ColourRows, [
    {'column': 'status', 'values': {'overdue': 'table-danger', 'pending': 'table-warning'}}
])

# Column totals in footer
table.add_plugin(ColumnTotals, {
    'amount': {'sum': True},
    'id': {'text': 'Total', 'css_class': 'text-danger'},
    'percentage': {'sum': 'percentage', 'numerator': 'vans', 'denominator': 'total', 'decimal_places': 1},
})

# Drag-and-drop row reordering
table.add_plugin(Reorder)
```

### Inline Editing

```python
def setup_table(table):
    table.edit_fields = ['first_name', 'title']
    table.edit_options = {'company__name': {'select2': True}}
```

### Row Actions (AJAX Commands)

Handle row-level actions from buttons:

```python
class MyView(DatatableView):
    ajax_commands = ['row']

    def row_delete(self, **kwargs):
        return self.command_response('delete_row', row_no=kwargs['row_no'], table_id=kwargs['table_id'])

    def row_toggle_tag(self, **kwargs):
        row_data = json.loads(kwargs['row_data'])
        # ... process action ...
        table = self.tables[kwargs['table_id']]
        return table.refresh_row(self.request, kwargs['row_no'])
```

### Data Export

```python
from django_datatables.downloads.excel_download import ExcelDownload
from django_datatables.downloads.clipboard import ClipboardCopy

class MyView(ExcelDownload, ClipboardCopy, DatatableView):
    model = MyModel

    def setup_menu(self):
        self.add_menu('menu', 'buttons').add_items(
            self.download_menu_item(),
            self.clipboard_menu_item(),
        )
        super().setup_menu()
```

### Multiple Tables Per View

```python
class TwoTableView(DatatableView):
    template_name = 'two_tables.html'

    def add_tables(self):
        self.add_table('t1', model=Company)
        self.add_table('t2', model=Person)

    @staticmethod
    def setup_t1(table):
        table.add_columns('id', 'name')

    @staticmethod
    def setup_t2(table):
        table.add_columns('id', 'first_name')
```

### Non-Model Data

Load data from any source (JSON files, APIs, etc.):

```python
class JsonTableView(DatatableView):

    @staticmethod
    def setup_table(table):
        table.add_columns(
            ColumnBase(column_name='field1'),
            ColumnBase(column_name='field2'),
        )

    @staticmethod
    def get_table_query(table, **kwargs):
        with open('data.json') as f:
            return json.load(f)
```

### Custom Column Classes

```python
from django_datatables.columns import DatatableColumn

class FullName(DatatableColumn):
    def col_setup(self):
        self.field = ['first_name', 'surname']

    def row_result(self, data_dict, _page_results):
        return f'{data_dict["first_name"]} {data_dict["surname"]}'
```

### Table Options

Common options passed via `table.table_options`:

```python
table.table_options['pageLength'] = 50
table.table_options['no_col_search'] = True
table.table_options['scrollX'] = True
table.table_options['ajax_url'] = '/custom/ajax/url/'
table.table_options['row_href'] = [render_replace(column='id', html='/detail/%1%/')]
```

## Demo Application

A Docker-based demo is included with sample data and 15+ examples covering filters, plugins, editing, rendering, and more.

```bash
docker-compose up
```

Then visit [http://localhost:8006](http://localhost:8006).

## Dependencies

- Python >= 3.6
- Django
- [django-ajax-helpers](https://github.com/jonesim/django-ajax-helpers) >= 0.0.16

Optional:
- `openpyxl` -- for Excel export
- `redis` -- for table caching

## License

MIT
