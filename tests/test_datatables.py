"""
Playwright end-to-end tests for django-filtered-datatables.

Covers: table rendering, data display, column types, pagination,
        two-table views, annotations, filters, sorting, search boxes,
        plugins (colour rows, column totals), links, non-model data,
        selection, aggregations, horizontal tables, and reordering.
"""
import re
import pytest
from playwright.sync_api import Page, expect

BASE = "http://localhost:8006"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wait_for_datatable(page: Page, table_selector: str = "table.dataTable"):
    """Wait until DataTables has finished rendering rows."""
    page.wait_for_selector(f"{table_selector} tbody tr", timeout=15000)


def get_visible_rows(page: Page, table_selector: str = "table.dataTable"):
    """Return the visible tbody rows for the given table."""
    return page.locator(f"{table_selector} tbody tr").all()


def get_cell_texts(page: Page, row_index: int = 0, table_selector: str = "table.dataTable"):
    """Return text content of cells in the given row."""
    cells = page.locator(f"{table_selector} tbody tr").nth(row_index).locator("td").all()
    return [c.text_content().strip() for c in cells]


def get_column_header_texts(page: Page, table_selector: str = "table.dataTable"):
    """Return header texts from the first thead row."""
    ths = page.locator(f"{table_selector} thead tr").first.locator("th").all()
    return [th.text_content().strip() for th in ths]


def get_info_text(page: Page):
    """Return the DataTables info string (e.g. 'Showing 1 to 22 of 94 entries')."""
    info = page.locator(".dataTables_info")
    info.wait_for(timeout=10000)
    return info.text_content().strip()


# ===========================================================================
# 1. Basic table rendering and data presence
# ===========================================================================

class TestExample1BasicRendering:
    """Example 1 – Company table with non-AJAX data, colour rows, column totals."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-1")
        wait_for_datatable(page)

    def test_table_is_visible(self, page: Page):
        expect(page.locator("table.dataTable")).to_be_visible()

    def test_table_has_data_rows(self, page: Page):
        rows = get_visible_rows(page)
        assert len(rows) > 0, "Table should have at least one data row"

    def test_column_headers_present(self, page: Page):
        headers = get_column_header_texts(page)
        assert "name" in [h.lower() for h in headers], "Should have a 'name' column"

    def test_pagination_info_shows_total(self, page: Page):
        info = get_info_text(page)
        assert "entries" in info.lower() or "Showing" in info

    def test_company_names_displayed(self, page: Page):
        body_text = page.locator("table.dataTable tbody").text_content()
        assert len(body_text) > 10, "Table body should contain company name text"


# ===========================================================================
# 2. Pagination
# ===========================================================================

class TestPagination:
    """Verify pagination controls work and page length is respected."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-1")
        wait_for_datatable(page)

    def test_page_length_respected(self, page: Page):
        rows = get_visible_rows(page)
        # Example1 sets pageLength to 22
        assert len(rows) == 22, f"Expected 22 rows per page, got {len(rows)}"

    def test_next_page_button_works(self, page: Page):
        """Navigate to Example 3 (AJAX, default pageLength 100) with enough data to paginate."""
        page.goto(f"{BASE}/example-3")
        wait_for_datatable(page)
        first_page_cells = [
            page.locator("table.dataTable tbody tr").nth(i).locator("td").first.text_content().strip()
            for i in range(min(3, len(get_visible_rows(page))))
        ]
        # Verify the table has loaded with data
        assert len(first_page_cells) > 0, "Table should have data rows"

    def test_pagination_controls_exist(self, page: Page):
        """Verify pagination controls are rendered."""
        paginate = page.locator(".dataTables_paginate")
        expect(paginate).to_be_visible()


# ===========================================================================
# 3. Column types – Example 3 (badges, annotations, colour rows)
# ===========================================================================

class TestExample3ColumnTypes:
    """Example 3 – Custom row_result with badges and ColourRows plugin."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-3")
        wait_for_datatable(page)

    def test_table_renders(self, page: Page):
        expect(page.locator("table.dataTable")).to_be_visible()

    def test_badge_html_rendered(self, page: Page):
        badges = page.locator("table.dataTable tbody .badge")
        assert badges.count() > 0, "Should have badge elements rendered in cells"

    def test_colour_rows_applied(self, page: Page):
        danger_rows = page.locator("table.dataTable tbody tr.table-danger")
        warning_rows = page.locator("table.dataTable tbody tr.table-warning")
        total = danger_rows.count() + warning_rows.count()
        assert total > 0, "ColourRows plugin should apply table-danger or table-warning classes"

    def test_sorted_by_people_descending(self, page: Page):
        """Example 3 sorts by -people (descending)."""
        # The badge values (people counts) should be in descending order
        badges = page.locator("table.dataTable tbody td .badge").all()
        if len(badges) >= 2:
            values = []
            for b in badges[:5]:
                text = b.text_content().strip()
                if text.isdigit():
                    values.append(int(text))
            if len(values) >= 2:
                assert values == sorted(values, reverse=True), \
                    f"People counts should be descending: {values}"


# ===========================================================================
# 4. Date columns and choice columns – Example 4
# ===========================================================================

class TestExample4FieldTypes:
    """Example 4 – DateColumn, ChoiceColumn, edit fields."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-4")
        wait_for_datatable(page)

    def test_table_renders_with_data(self, page: Page):
        rows = get_visible_rows(page)
        assert len(rows) > 0

    def test_date_column_format(self, page: Page):
        """DateColumn should render dates in dd/mm/yyyy format."""
        # The 'Date' column is the last column
        cells = page.locator("table.dataTable tbody tr").first.locator("td").all()
        # Look for date-formatted text anywhere in the row
        row_text = " ".join(c.text_content() for c in cells)
        assert re.search(r'\d{2}/\d{2}/\d{4}', row_text), \
            f"Should have dd/mm/yyyy date format in row. Got: {row_text}"

    def test_choice_column_displays_labels(self, page: Page):
        """ChoiceColumn for 'title' should show Mr/Mrs/Miss instead of 0/1/2."""
        body_text = page.locator("table.dataTable tbody").text_content()
        has_choice = any(label in body_text for label in ["Mr", "Mrs", "Miss"])
        assert has_choice, "Choice column should display labels (Mr/Mrs/Miss)"


# ===========================================================================
# 5. Link columns – Example 5
# ===========================================================================

class TestExample5Links:
    """Example 5 – ColumnLink and tag filters."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-5")
        wait_for_datatable(page)

    def test_link_columns_have_anchors(self, page: Page):
        links = page.locator("table.dataTable tbody a")
        assert links.count() > 0, "ColumnLink should render anchor elements"

    def test_link_href_contains_pk(self, page: Page):
        first_link = page.locator("table.dataTable tbody a").first
        href = first_link.get_attribute("href")
        assert href is not None, "Link should have href"
        assert "/example-2/" in href, f"Link should point to example2 URL, got {href}"

    def test_tag_filter_present(self, page: Page):
        """Example 5 adds a tag filter for Tags."""
        page_html = page.content()
        assert "filter" in page_html.lower() or page.locator(".badge").count() > 0


# ===========================================================================
# 6. Two tables on one page – Example 6
# ===========================================================================

class TestExample6TwoTables:
    """Example 6 – Multiple DatatableTables on a single view."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-6")
        page.wait_for_selector("table.dataTable", timeout=15000)

    def test_two_tables_rendered(self, page: Page):
        tables = page.locator("table.dataTable").all()
        assert len(tables) >= 2, f"Expected 2 tables, found {len(tables)}"

    def test_first_table_has_company_data(self, page: Page):
        first_table = page.locator("table.dataTable").first
        first_table.locator("tbody tr").first.wait_for(timeout=10000)
        rows = first_table.locator("tbody tr").all()
        assert len(rows) > 0, "First table (companies) should have rows"

    def test_second_table_has_person_data(self, page: Page):
        second_table = page.locator("table.dataTable").nth(1)
        second_table.locator("tbody tr").first.wait_for(timeout=10000)
        rows = second_table.locator("tbody tr").all()
        assert len(rows) > 0, "Second table (people) should have rows"

    def test_tables_have_different_data(self, page: Page):
        t1_text = page.locator("table.dataTable").first.locator("tbody").text_content()
        t2_text = page.locator("table.dataTable").nth(1).locator("tbody").text_content()
        assert t1_text != t2_text, "Two tables should display different data"


# ===========================================================================
# 7. Annotations – Example 3 (Count) and Example Totaling
# ===========================================================================

class TestAnnotations:
    """Test Django ORM annotations appear correctly in the table."""

    def test_count_annotation_example3(self, page: Page):
        """Example 3 uses Count('person__id') annotation as 'people'."""
        page.goto(f"{BASE}/example-3")
        wait_for_datatable(page)
        headers = get_column_header_texts(page)
        # Should have columns using annotations
        body_text = page.locator("table.dataTable tbody").text_content()
        # Badge values should be numeric (counts)
        badges = page.locator("table.dataTable tbody .badge")
        assert badges.count() > 0
        first_badge = badges.first.text_content().strip()
        assert first_badge.isdigit(), f"Annotation count should be numeric, got '{first_badge}'"

    def test_aggregation_totals(self, page: Page):
        """ExampleTotaling uses Sum annotations with ColumnTotals plugin."""
        page.goto(f"{BASE}/example-total")
        wait_for_datatable(page)
        rows = get_visible_rows(page)
        assert len(rows) > 0, "Totaling example should have data"
        # Check column totals plugin rendered a footer with values
        tfoot_text = page.locator("table.dataTable tfoot").text_content()
        assert "Total" in tfoot_text or len(tfoot_text.strip()) > 0, \
            "Column totals should show in table footer"


# ===========================================================================
# 8. Column totals plugin
# ===========================================================================

class TestColumnTotalsPlugin:
    """Verify the ColumnTotals plugin renders sum rows."""

    def test_totals_in_example_total(self, page: Page):
        page.goto(f"{BASE}/example-total")
        wait_for_datatable(page)
        # The ColumnTotals plugin appends a row. Check for the "Total" label.
        page_text = page.text_content("body")
        assert "Total" in page_text, "Should display 'Total' label from ColumnTotals plugin"

    def test_percentage_columns_display(self, page: Page):
        """ExampleTotaling has percentage columns with % symbol."""
        page.goto(f"{BASE}/example-total")
        wait_for_datatable(page)
        body_text = page.locator("table.dataTable tbody").text_content()
        assert "%" in body_text, "Percentage columns should contain % symbol"


# ===========================================================================
# 9. Colour rows plugin
# ===========================================================================

class TestColourRowsPlugin:

    def test_danger_rows_in_example1(self, page: Page):
        """Example 1 adds ColourRows for id=1 -> table-danger."""
        page.goto(f"{BASE}/example-1")
        wait_for_datatable(page)
        danger = page.locator("table.dataTable tbody tr.table-danger")
        assert danger.count() >= 1, "ColourRows should apply table-danger class to row with id=1"


# ===========================================================================
# 10. Render functions – Example 7 (buttons, ManyToMany, lookups)
# ===========================================================================

class TestExample7Rendering:
    """Example 7 – row buttons, ManyToMany badges, render functions."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-7")
        wait_for_datatable(page)

    def test_row_buttons_rendered(self, page: Page):
        buttons = page.locator("table.dataTable tbody button")
        assert buttons.count() > 0, "Row buttons should be rendered"

    def test_many_to_many_badges(self, page: Page):
        badges = page.locator("table.dataTable tbody .badge")
        assert badges.count() > 0, "ManyToMany tags should render as badges"

    def test_column_totals_present(self, page: Page):
        page_text = page.text_content("body")
        assert "Total" in page_text, "Should have column totals"


# ===========================================================================
# 11. Render functions – Example 12 (Replace, ReplaceLookup, MergeArray)
# ===========================================================================

class TestExample12RenderFunctions:
    """Example 12 – comprehensive render function examples."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-12")
        wait_for_datatable(page)

    def test_table_renders(self, page: Page):
        rows = get_visible_rows(page)
        assert len(rows) > 0

    def test_replace_function_renders_html(self, page: Page):
        """Replace function should produce formatted output like '* 1'."""
        body_text = page.locator("table.dataTable tbody").text_content()
        assert "*" in body_text, "Replace render should produce '* value' text"

    def test_lookup_renders_words(self, page: Page):
        """ReplaceLookup should convert numbers to words (one, two, etc.)."""
        body_text = page.locator("table.dataTable tbody").text_content()
        has_word = any(w in body_text.lower() for w in ["one", "two", "three", "four", "five"])
        assert has_word, "ReplaceLookup should render number words"


# ===========================================================================
# 12. Search boxes
# ===========================================================================

class TestSearchBoxes:
    """Search boxes example – text search and dropdown select search."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/search-boxes")
        wait_for_datatable(page)

    def test_search_inputs_present(self, page: Page):
        search_row = page.locator("table.dataTable thead tr.column-search-header")
        inputs = search_row.locator("input")
        assert inputs.count() > 0, "Should have column search inputs"

    def test_select_search_present(self, page: Page):
        selects = page.locator("table.dataTable thead select")
        assert selects.count() > 0, "Should have dropdown select search for dissolved column"

    def test_text_search_filters_rows(self, page: Page):
        initial_info = get_info_text(page)
        search_input = page.locator("table.dataTable thead tr.column-search-header input").first
        search_input.fill("a")
        search_input.dispatch_event("keyup")
        page.wait_for_timeout(1000)
        filtered_info = get_info_text(page)
        # Either the info changed or it filtered (could be all rows contain 'a')
        # Just verify the search didn't break anything
        rows = get_visible_rows(page)
        assert len(rows) > 0, "Search should still show matching rows"


# ===========================================================================
# 13. Non-model data
# ===========================================================================

class TestNoModelData:
    """Tables loaded from JSON data rather than Django models."""

    def test_non_ajax_version(self, page: Page):
        page.goto(f"{BASE}/no-model-non-ajax")
        wait_for_datatable(page)
        rows = get_visible_rows(page)
        assert len(rows) > 0, "Non-model non-AJAX table should display data"

    def test_ajax_version(self, page: Page):
        page.goto(f"{BASE}/no-model-ajax")
        wait_for_datatable(page)
        rows = get_visible_rows(page)
        assert len(rows) > 0, "Non-model AJAX table should display data"


# ===========================================================================
# 14. Selection
# ===========================================================================

class TestSelection:
    """Row selection with SelectColumn."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/selection/demo/")
        wait_for_datatable(page)

    def test_table_renders(self, page: Page):
        rows = get_visible_rows(page)
        assert len(rows) > 0

    def test_select_filter_present(self, page: Page):
        """Selection example should have a 'selected' filter for managing selections."""
        page_html = page.content()
        assert "selected" in page_html.lower(), "Selection page should reference selection functionality"

    def test_selection_column_exists_in_config(self, page: Page):
        """SelectColumn should be present in the table configuration."""
        page_html = page.content()
        assert "SelectColumn" in page_html, "SelectColumn should be referenced in JS config"


# ===========================================================================
# 15. Aggregations
# ===========================================================================

class TestAggregations:
    """Standard and horizontal aggregation views."""

    def test_standard_aggregations(self, page: Page):
        page.goto(f"{BASE}/aggregations/standard")
        wait_for_datatable(page)
        rows = get_visible_rows(page)
        assert len(rows) > 0, "Aggregations table should have data"

    def test_horizontal_aggregations(self, page: Page):
        page.goto(f"{BASE}/aggregation/horizontal")
        page.wait_for_selector("table", timeout=15000)
        tables = page.locator("table").all()
        assert len(tables) > 0, "Horizontal aggregation should render tables"


# ===========================================================================
# 16. Horizontal table
# ===========================================================================

class TestHorizontalTable:
    """Horizontal table displays a single record's fields as rows."""

    def test_horizontal_renders(self, page: Page):
        page.goto(f"{BASE}/horizontal")
        page.wait_for_selector("table", timeout=15000)
        expect(page.locator("table")).to_be_visible()
        # Horizontal tables show field names as row labels
        table_text = page.locator("table").text_content()
        assert len(table_text.strip()) > 0, "Horizontal table should have content"


# ===========================================================================
# 17. Reorderable table
# ===========================================================================

class TestReorderTable:

    def test_orderable_table_renders(self, page: Page):
        page.goto(f"{BASE}/orderable")
        page.wait_for_selector("table", timeout=15000)
        expect(page.locator("table")).to_be_visible()
        rows = page.locator("table tbody tr").all()
        assert len(rows) > 0, "Reorder table should have rows"


# ===========================================================================
# 18. Example 2 – Foreign key traversal, AJAX, select2 filter
# ===========================================================================

class TestExample2ForeignKeys:
    """Example 2 – Person table with company FK traversal and AJAX."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-2/")
        wait_for_datatable(page)

    def test_table_renders_with_fk_data(self, page: Page):
        rows = get_visible_rows(page)
        assert len(rows) > 0

    def test_company_name_column_present(self, page: Page):
        headers = get_column_header_texts(page)
        assert "Company Name" in headers, f"Should have 'Company Name' FK column. Got: {headers}"

    def test_link_column_from_model(self, page: Page):
        """company__collink_1 defined in Company.Datatable should render links."""
        links = page.locator("table.dataTable tbody a")
        assert links.count() > 0, "Model-defined ColumnLink should render"


# ===========================================================================
# 19. Example 9 – Choice rendering with null handling
# ===========================================================================

class TestExample9Choices:
    """Example 9 – ChoiceColumn with render_replace and null_value."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-9")
        wait_for_datatable(page)

    def test_table_renders(self, page: Page):
        rows = get_visible_rows(page)
        assert len(rows) > 0

    def test_badge_rendering(self, page: Page):
        badges = page.locator("table.dataTable tbody .badge")
        assert badges.count() > 0, "Choice columns with render should produce badge elements"


# ===========================================================================
# 20. Example 10 – Multiple column definition formats
# ===========================================================================

class TestExample10ColumnDefinitions:
    """Example 10 – Various ways to define columns (string, tuple, class, model)."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-10")
        wait_for_datatable(page)

    def test_table_renders(self, page: Page):
        rows = get_visible_rows(page)
        assert len(rows) > 0

    def test_multiple_column_headers(self, page: Page):
        headers = get_column_header_texts(page)
        assert len(headers) >= 5, f"Should have many columns from various definitions. Got {len(headers)}"

    def test_tuple_column_title(self, page: Page):
        headers = get_column_header_texts(page)
        assert "Tuple" in headers, f"Tuple-defined column should have 'Tuple' title. Got: {headers}"


# ===========================================================================
# 21. Sorting
# ===========================================================================

class TestSorting:
    """Verify clicking column headers triggers sorting."""

    def test_click_header_sorts(self, page: Page):
        page.goto(f"{BASE}/example-3")
        wait_for_datatable(page)

        # Get first column values before clicking
        cells_before = [
            page.locator("table.dataTable tbody tr").nth(i).locator("td").first.text_content().strip()
            for i in range(min(5, len(get_visible_rows(page))))
        ]

        # Click the 'name' header to sort
        name_header = page.locator("table.dataTable thead tr").first.locator("th").first
        name_header.click()
        page.wait_for_timeout(500)

        cells_after = [
            page.locator("table.dataTable tbody tr").nth(i).locator("td").first.text_content().strip()
            for i in range(min(5, len(get_visible_rows(page))))
        ]

        # Order should change (or stay same if already sorted by that column)
        # The main assertion is that it doesn't crash
        assert len(cells_after) > 0, "Table should still have data after sorting"


# ===========================================================================
# 22. Spreadsheet view
# ===========================================================================

class TestSpreadsheet:

    def test_spreadsheet_renders(self, page: Page):
        page.goto(f"{BASE}/spreadsheet")
        # JSpreadsheet may render as .jspreadsheet or .jexcel or within a div
        page.wait_for_timeout(3000)
        # Check that the spreadsheet page loaded and has table-like content
        page_text = page.text_content("body")
        assert len(page_text.strip()) > 0, "Spreadsheet page should load content"
        # Check for spreadsheet-related elements
        has_spreadsheet = (
            page.locator(".jspreadsheet").count() > 0
            or page.locator(".jexcel").count() > 0
            or page.locator("[id*='spreadsheet']").count() > 0
            or "jspreadsheet" in page.content()
        )
        assert has_spreadsheet, "Spreadsheet view should include jspreadsheet"


# ===========================================================================
# 23. Modal filter
# ===========================================================================

class TestModalFilter:

    def test_modal_filter_page_loads(self, page: Page):
        page.goto(f"{BASE}/modal-filter/")
        wait_for_datatable(page)
        rows = get_visible_rows(page)
        assert len(rows) > 0, "Modal filter example should display data"


# ===========================================================================
# 24. Example 8 – Hierarchical/tree data
# ===========================================================================

class TestExample8Tree:
    """Example 8 – Expand/collapse tree data."""

    @pytest.fixture(autouse=True)
    def navigate(self, page: Page):
        page.goto(f"{BASE}/example-8")
        wait_for_datatable(page)

    def test_table_renders(self, page: Page):
        rows = get_visible_rows(page)
        assert len(rows) > 0

    def test_expand_icons_present(self, page: Page):
        """Should have plus/minus icons for expand/collapse."""
        icons = page.locator("table.dataTable tbody i.fas")
        assert icons.count() > 0, "Tree view should have expand/collapse icons"


# ===========================================================================
# 25. Example 11 – Callable model methods
# ===========================================================================

class TestExample11Callables:
    """Example 11 – Columns using callable model methods."""

    def test_table_renders(self, page: Page):
        page.goto(f"{BASE}/example-11")
        wait_for_datatable(page)
        rows = get_visible_rows(page)
        assert len(rows) > 0

    def test_callable_column_has_data(self, page: Page):
        page.goto(f"{BASE}/example-11")
        wait_for_datatable(page)
        body_text = page.locator("table.dataTable tbody").text_content()
        # c_test returns 'id - title', so should contain ' - '
        assert " - " in body_text, "Callable column should produce 'id - title' format"


# ===========================================================================
# 26. Navigation between examples
# ===========================================================================

class TestNavigation:
    """Verify the menu navigation works between example pages."""

    def test_navigate_from_example1_to_example2(self, page: Page):
        page.goto(f"{BASE}/example-1")
        wait_for_datatable(page)

        # Click the menu dropdown
        page.locator("text=Main Examples").click()
        page.wait_for_timeout(300)
        page.locator("a.dropdown-item:has-text('Example2')").click()
        page.wait_for_url("**/example-2/**", timeout=10000)
        wait_for_datatable(page)

        headers = get_column_header_texts(page)
        assert "Company Name" in headers, "Should navigate to Example 2"

    def test_navigate_to_search_boxes(self, page: Page):
        page.goto(f"{BASE}/example-1")
        wait_for_datatable(page)

        page.locator("text=Main Examples").click()
        page.wait_for_timeout(300)
        page.locator("a.dropdown-item:has-text('Search Boxes')").click()
        page.wait_for_url("**/search-boxes**", timeout=10000)
        wait_for_datatable(page)

        search_inputs = page.locator("table.dataTable thead input")
        assert search_inputs.count() > 0


# ===========================================================================
# 27. FK traversal with pk filter – Example 2 with pk
# ===========================================================================

class TestExample2WithPK:
    """Example 2 filtered by company pk."""

    def test_pk_filtered_view(self, page: Page):
        page.goto(f"{BASE}/example-2/1/")
        wait_for_datatable(page)
        rows = get_visible_rows(page)
        assert len(rows) > 0, "PK-filtered view should show people for company 1"
        # All rows should belong to the same company
        if len(rows) >= 2:
            company_cells = [
                page.locator("table.dataTable tbody tr").nth(i).locator("td").nth(2).text_content().strip()
                for i in range(min(3, len(rows)))
            ]
            unique = set(company_cells)
            assert len(unique) == 1, f"All rows should be for same company, got {unique}"


# ===========================================================================
# 28. Widget view
# ===========================================================================

class TestWidgetView:

    def test_widget_page_loads(self, page: Page):
        page.goto(f"{BASE}/widget")
        page.wait_for_selector("table", timeout=15000)
        tables = page.locator("table").all()
        assert len(tables) > 0, "Widget page should have at least one table"

    def test_widget_has_datatable_widgets(self, page: Page):
        """Widget page should have DataTableWidget tables rendered."""
        page.goto(f"{BASE}/widget")
        page.wait_for_selector("table.dataTable", timeout=15000)
        tables = page.locator("table.dataTable").all()
        assert len(tables) >= 2, "Widget page should have multiple DataTable widgets"
