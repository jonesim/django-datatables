from dataclasses import dataclass


@dataclass(frozen=True)
class PageRef:
    url_name: str
    title: str


@dataclass(frozen=True)
class Chapter:
    title: str
    pages: tuple


# The manual's table of contents. Drives both the navigation bar dropdowns
# and the contents page, so adding a page here is all that is needed to
# publish it in the manual.
CHAPTERS = (
    Chapter('Getting Started', (
        PageRef('first_table', 'A First Table'),
        PageRef('column_definitions', 'Ways to Define Columns'),
        PageRef('column_parameters', 'Column Parameters'),
    )),
    Chapter('Columns', (
        PageRef('column_links', 'Column Links'),
        PageRef('tag_columns', 'Tags & Badges (Many-to-Many)'),
        PageRef('column_visibility', 'Column Visibility'),
        PageRef('aggregations', 'Aggregations'),
        PageRef('aggregations_horizontal', 'Aggregations (Horizontal)'),
    )),
    Chapter('Rendering', (
        PageRef('render_functions', 'Render Functions'),
        PageRef('html_rendering', 'Server vs Client HTML'),
        PageRef('choice_rendering', 'Choices & Null Values'),
    )),
    Chapter('Editing & Actions', (
        PageRef('inline_editing', 'Inline Editing'),
        PageRef('row_buttons', 'Row Buttons'),
    )),
    Chapter('Filters', (
        PageRef('pivot_select2_filters', 'Pivot & Select2'),
        PageRef('tag_filter', 'Tag Filter'),
        PageRef('date_filter', 'Date Filter'),
        PageRef('totals_filter', 'Totals Filter'),
        PageRef('row_tree', 'Row Expansion (Tree)'),
        PageRef('custom_js_filter', 'Custom JavaScript Filter'),
        PageRef('search_boxes', 'Search Boxes'),
        PageRef('modal_filter', 'Modal Filter'),
    )),
    Chapter('Server-side Tables', (
        PageRef('server_side', 'Pagination & Search'),
        PageRef('server_side_tags', 'Tag Filter'),
        PageRef('server_side_totals', 'Totals Filter'),
        PageRef('server_side_json', 'JSON Column Filter'),
    )),
    Chapter('Plugins', (
        PageRef('column_totals', 'Column Totals'),
        PageRef('row_reorder', 'Row Reorder'),
        PageRef('save_filters', 'Save Filters'),
    )),
    Chapter('Selection & Downloads', (
        PageRef('selection', 'Row Selection'),
        PageRef('downloads', 'Excel, Clipboard & CSV'),
    )),
    Chapter('Layout', (
        PageRef('multiple_tables', 'Multiple Tables'),
        PageRef('horizontal', 'Horizontal Table'),
        PageRef('no_model', 'Table Without a Model'),
        PageRef('form_widgets', 'Form Widgets'),
        PageRef('spreadsheet', 'Spreadsheet'),
    )),
)
