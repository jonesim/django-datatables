from django.urls import path
from django.views.generic.base import RedirectView

from datatable_examples.views import (columns, downloads, editing, filters, getting_started, layout, plugins,
                                      rendering, server_side)

urlpatterns = [
    path('', getting_started.ManualIndex.as_view(), name='manual_index'),
    path('datatable-redirect/', RedirectView.as_view(pattern_name='manual_index'),
         name='django-filtered-datatables'),

    # Getting started
    path('getting-started/first-table', getting_started.FirstTable.as_view(), name='first_table'),
    path('getting-started/column-definitions', getting_started.ColumnDefinitions.as_view(),
         name='column_definitions'),
    path('getting-started/column-parameters', getting_started.ColumnParameters.as_view(), name='column_parameters'),

    # Columns
    path('columns/links', columns.ColumnLinks.as_view(), name='column_links'),
    path('columns/tags-and-badges', columns.TagColumns.as_view(), name='tag_columns'),
    path('columns/visibility', columns.ColumnVisibility.as_view(), name='column_visibility'),
    path('columns/visibility/<int:pk>', columns.ColumnVisibility.as_view(), name='column_visibility'),
    path('columns/aggregations', columns.Aggregations.as_view(), name='aggregations'),
    path('columns/aggregations-horizontal', columns.AggregationsHorizontal.as_view(),
         name='aggregations_horizontal'),

    # Rendering
    path('rendering/render-functions', rendering.RenderFunctions.as_view(), name='render_functions'),
    path('rendering/server-vs-client-html', rendering.HtmlRendering.as_view(), name='html_rendering'),
    path('rendering/choices-and-null-values', rendering.ChoiceRendering.as_view(), name='choice_rendering'),

    # Editing & actions
    path('editing/inline-editing', editing.InlineEditing.as_view(), name='inline_editing'),
    path('editing/row-buttons', editing.RowButtons.as_view(), name='row_buttons'),

    # Filters
    path('filters/pivot-and-select2', filters.PivotSelect2Filters.as_view(), name='pivot_select2_filters'),
    path('filters/tag', filters.TagFilter.as_view(), name='tag_filter'),
    path('filters/date', filters.DateFilter.as_view(), name='date_filter'),
    path('filters/totals', filters.TotalsFilter.as_view(), name='totals_filter'),
    path('filters/row-expansion', filters.RowTree.as_view(), name='row_tree'),
    path('filters/custom-javascript', filters.CustomJsFilter.as_view(), name='custom_js_filter'),
    path('filters/search-boxes', filters.SearchBoxes.as_view(), name='search_boxes'),
    path('filters/modal', filters.ModalFilter.as_view(), name='modal_filter'),
    path('filters/modal/<str:base64>', filters.ModalFilter.as_view(), name='modal_filter'),

    # Server-side tables
    path('server-side/pagination', server_side.ServerSidePagination.as_view(), name='server_side'),
    path('server-side/tag-filter', server_side.ServerSideTagFilter.as_view(), name='server_side_tags'),
    path('server-side/totals-filter', server_side.ServerSideTotalsFilter.as_view(), name='server_side_totals'),
    path('server-side/json-column', server_side.ServerSideJsonColumn.as_view(), name='server_side_json'),

    # Plugins
    path('plugins/column-totals', plugins.ColumnTotalsPage.as_view(), name='column_totals'),
    path('plugins/reorder', plugins.RowReorder.as_view(), name='row_reorder'),
    path('plugins/save-filters', plugins.SaveFilters.as_view(), name='save_filters'),

    # Selection & downloads
    path('selection/checkboxes', downloads.RowSelection.as_view(), name='selection'),
    path('downloads/excel-clipboard-csv', downloads.Downloads.as_view(), name='downloads'),

    # Layout
    path('layout/multiple-tables', layout.MultipleTables.as_view(), name='multiple_tables'),
    path('layout/horizontal', layout.HorizontalTablePage.as_view(), name='horizontal'),
    path('layout/no-model', layout.NoModelData.as_view(), name='no_model'),
    path('layout/widgets', layout.FormWidgets.as_view(), name='form_widgets'),
    path('layout/spreadsheet', layout.SpreadsheetPage.as_view(), name='spreadsheet'),
    path('layout/spreadsheet-modal', layout.SpreadsheetModal.as_view(), name='spreadsheet_modal'),

    # Legacy URLs from before the manual restructure
    path('example-1', RedirectView.as_view(pattern_name='modal_filter')),
    path('example-1/<str:base64>/', RedirectView.as_view(pattern_name='modal_filter')),
    path('example-2/', RedirectView.as_view(pattern_name='column_visibility')),
    path('example-2/<int:pk>/', RedirectView.as_view(pattern_name='column_visibility')),
    path('example-3', RedirectView.as_view(pattern_name='html_rendering')),
    path('example-4', RedirectView.as_view(pattern_name='date_filter')),
    path('example-5', RedirectView.as_view(pattern_name='tag_filter')),
    path('example-6', RedirectView.as_view(pattern_name='multiple_tables')),
    path('example-7', RedirectView.as_view(pattern_name='row_buttons')),
    path('example-8', RedirectView.as_view(pattern_name='row_tree')),
    path('example-9', RedirectView.as_view(pattern_name='choice_rendering')),
    path('example-10', RedirectView.as_view(pattern_name='column_definitions')),
    path('example-11', RedirectView.as_view(pattern_name='column_parameters')),
    path('example-12', RedirectView.as_view(pattern_name='render_functions')),
    path('example-total', RedirectView.as_view(pattern_name='column_totals')),
    path('search-boxes', RedirectView.as_view(pattern_name='search_boxes')),
    path('no-model-ajax', RedirectView.as_view(pattern_name='no_model')),
    path('no-model-non-ajax', RedirectView.as_view(pattern_name='no_model')),
    path('orderable', RedirectView.as_view(pattern_name='row_reorder')),
    path('widget', RedirectView.as_view(pattern_name='form_widgets')),
    path('aggregations/standard', RedirectView.as_view(pattern_name='aggregations')),
    path('aggregation/horizontal', RedirectView.as_view(pattern_name='aggregations_horizontal')),
    path('selection/demo/', RedirectView.as_view(pattern_name='selection')),
    path('horizontal', RedirectView.as_view(pattern_name='horizontal')),
    path('modal-filter/', RedirectView.as_view(pattern_name='modal_filter')),
    path('modal-filter/<str:base64>/', RedirectView.as_view(pattern_name='modal_filter')),
    path('spreadsheet', RedirectView.as_view(pattern_name='spreadsheet')),
    path('spreadsheet_modal', RedirectView.as_view(pattern_name='spreadsheet_modal')),
    path('server-side', RedirectView.as_view(pattern_name='server_side')),
    path('server-side-tags', RedirectView.as_view(pattern_name='server_side_tags')),
    path('server-side-totals', RedirectView.as_view(pattern_name='server_side_totals')),
    path('server-side-json', RedirectView.as_view(pattern_name='server_side_json')),
    path('hide-columns', RedirectView.as_view(pattern_name='column_visibility')),
]
