import json
import logging

from django.db.models import Q

from django_datatables.datatables.datatable_error import DatatableError
from django_datatables.datatables.datatable_table import DatatableTable
from django_datatables.filters import DatatableFilter
from django_datatables.server_side_filters import (ServerDatatableFilter, ServerDateFilter, ServerPivotFilter,
                                                   ServerSelect2Filter, ServerTagFilter, ServerTotalsFilter)

logger = logging.getLogger(__name__)


class ServerSideTable(DatatableTable):
    """
    DatatableTable variant that uses DataTables.js server-side processing.

    Each page request is handled by the server: the ORM applies filtering,
    ordering, and slicing rather than loading all rows into the browser.

    Usage
    -----
    Set ``server_side = True`` on the view and the default ``add_tables()``
    creates a ``ServerSideTable`` automatically:

        class MyView(DatatableView):
            server_side = True
            model = MyModel

    For per-table control (e.g. mixing server-side and client-side tables in
    one view) pass the class explicitly when calling ``add_table()``:

        def add_tables(self):
            self.add_table('mytable', model=MyModel, table_class=ServerSideTable)

    The JavaScript side is activated automatically when ``serverSide: True``
    appears in ``table_options`` — ``ServerSideTable`` sets this by default.

    Filtering
    ---------
    ``search_fields`` is an optional list of ORM field paths that the global
    search box queries.  When empty the table falls back to searching all
    non-calculated single-field columns with ``icontains``.  Column-header
    search boxes always search the column's own ORM field.

    Column search-box visibility
    ----------------------------
    Search input boxes are suppressed automatically for columns that cannot be
    filtered server-side: calculated fields (prefixed with ``_``), JS-rendered
    columns, multi-field columns, and columns with no ORM field.

    Override per column by passing a keyword argument when the column is
    declared::

        DatatableColumn('status', no_col_search=True)   # always hidden
        DatatableColumn('notes',  no_col_search=False)  # always shown

    To hide every column search box for the whole table::

        class MyTable(ServerSideTable):
            table_options = {'no_col_search': True}

    COUNT query behaviour
    ---------------------
    Every page request issues at most two COUNT queries: one for
    ``recordsTotal`` (all rows matching the view's base filters) and one for
    ``recordsFiltered`` (rows after the user's search).  The second COUNT is
    skipped automatically when no search is active.

    For very large tables where even a single COUNT is too expensive, set
    ``approximate_count = True``.  This uses PostgreSQL's ``pg_class.reltuples``
    statistic for ``recordsTotal`` (updated by VACUUM/ANALYZE, accurate to
    within a few percent) and falls back to a real COUNT for
    ``recordsFiltered`` only when a search is active.  On other databases the
    flag is silently ignored and a normal COUNT is used.

    JS filters
    ----------
    ``add_js_filters`` supports the ``pivot``, ``select2``, ``date``,
    ``tag``, and ``totals`` filters.  They are transparently swapped for
    server-side equivalents (see ``django_datatables.server_side_filters``):
    selections are applied as ORM WHERE clauses and the
    ``[filtered / total]`` count badges are computed with GROUP BY aggregate
    queries.  ``tag`` filters (ManyToManyColumn) make the queryset
    ``distinct()`` to avoid duplicate rows from the M2M join; ``totals``
    filters show ``Sum(sum_column)`` in the badges instead of row counts.

    ``tag`` filters on custom tag columns (plain ``DatatableColumn``
    subclasses with a ``lookup`` that build their tag ids in
    ``setup_results``) need the ORM path from the table model to the tag
    values passed explicitly, as the column itself carries no field
    information::

        table.add_js_filters('tag', 'Tags', field='tags__pk')

    Facet counts are only recomputed when the filter/search state changes —
    the client sends ``need_facets=1`` on those requests and the response
    carries a ``facets`` key.  Paging and sorting never trigger the aggregate
    queries.  Each state change costs two GROUP BY queries per counted facet
    (totals on the base queryset, filtered counts on the searched/filtered
    queryset).  Columns with more distinct values than ``max_facet_values``
    (default 200, pass as a kwarg to ``add_js_filters``) skip counts and show
    a message instead.

    Limitations
    -----------
    * The ``expand`` and ``selected`` JS filters are not supported
      server-side; requesting one raises ``DatatableError``.
    * Facet totals are recomputed on every filter/search change; caching them
      (e.g. in Redis via ``django_datatables.cache``) is possible future work
      for very large tables.
    * ``ColumnTotalsPlugin`` footer sums only cover the current page.
    """

    # JS filter types that have a server-side implementation.
    server_js_filters = {
        'pivot': ServerPivotFilter,
        'select2': ServerSelect2Filter,
        'date': ServerDateFilter,
        'tag': ServerTagFilter,
        'totals': ServerTotalsFilter,
    }

    # Override in a subclass or instance to restrict global search to specific
    # ORM paths, e.g. ['name', 'company__name', 'email'].
    search_fields = []

    # Set True to use fast PostgreSQL table-statistics estimate for
    # recordsTotal instead of COUNT(*).  Ignored on non-PostgreSQL databases.
    approximate_count = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tell DataTables.js to operate in server-side mode.
        self.table_options['serverSide'] = True

    # ------------------------------------------------------------------
    # JS filters
    # ------------------------------------------------------------------

    def add_js_filters(self, name_or_template, *column_ids, filter_class=DatatableFilter, **kwargs):
        """Substitute server-side filter classes for the supported types.

        ``table.add_js_filters('pivot', 'column')`` works unchanged on a
        server-side table.  Unsupported built-in types raise a clear error;
        explicit ``filter_class=`` or custom template paths pass through.
        """
        if filter_class is DatatableFilter and isinstance(name_or_template, str):
            if name_or_template in self.server_js_filters:
                filter_class = self.server_js_filters[name_or_template]
            elif name_or_template in DatatableFilter.template_library:
                raise DatatableError(f"JS filter '{name_or_template}' is not supported with ServerSideTable. "
                                     f"Supported types: {', '.join(self.server_js_filters)}")
        super().add_js_filters(name_or_template, *column_ids, filter_class=filter_class, **kwargs)

    def _server_filters(self):
        return [f for f in self.js_filter_list if isinstance(f, ServerDatatableFilter)]

    @staticmethod
    def _parse_js_filter_state(post_data):
        try:
            state = json.loads(post_data.get('js_filter_state') or '{}')
        except (ValueError, TypeError):
            return {}
        return state if isinstance(state, dict) else {}

    def _apply_js_filters(self, queryset, filter_state):
        """Apply posted filter selections; returns (queryset, any_applied)."""
        applied = False
        for js_filter in self._server_filters():
            state = filter_state.get(js_filter.column.column_name)
            if not isinstance(state, dict):
                continue
            try:
                queryset = js_filter.apply_filter(queryset, state)
                applied = True
            except Exception:
                logger.exception('Error applying server-side js filter on %s', js_filter.column.column_name)
        return queryset, applied

    def _build_facets(self, base_queryset, filtered_queryset):
        facets = {}
        for js_filter in self._server_filters():
            if not js_filter.has_facets:
                continue
            try:
                facets[js_filter.column.column_name] = js_filter.get_facets(base_queryset, filtered_queryset)
            except Exception:
                logger.exception('Error building facets for %s', js_filter.column.column_name)
        return facets

    # ------------------------------------------------------------------
    # Column search-box visibility
    # ------------------------------------------------------------------

    def add_columns(self, *columns):
        """Add columns and auto-hide search boxes for non-searchable columns.

        A search box is suppressed automatically when the column cannot be
        filtered server-side (calculated fields, JS-rendered values, multi-
        field columns, or columns with no ORM field).  Developers can override
        this behaviour per column:

        * ``no_col_search=True``  — always hide the search box
        * ``no_col_search=False`` — always show it (even if non-searchable)

        To hide all search boxes for the table, set::

            table_options = {'no_col_search': True}
        """
        super().add_columns(*columns)
        self._auto_mark_unsearchable_columns()

    def _is_col_searchable(self, col):
        """Return True if the column can be filtered with a server-side icontains lookup."""
        return (
            col.field
            and isinstance(col.field, str)
            and 'calculated' not in col.options
        )

    def _auto_mark_unsearchable_columns(self):
        """Set no_col_search on columns whose search box would silently do nothing."""
        for col in self.columns:
            if 'no_col_search' not in col.options:
                if not self._is_col_searchable(col):
                    col.options['no_col_search'] = True

    # ------------------------------------------------------------------
    # Queryset building
    # ------------------------------------------------------------------

    def get_query(self, **kwargs):
        """Return an unsliced queryset.

        Server-side pagination slices after counting, so ``max_records``
        truncation is suppressed here.  The developer can still set
        ``self.max_records`` to impose a hard cap in
        ``get_server_side_json``.
        """
        saved = self.max_records
        self.max_records = None
        try:
            return super().get_query(**kwargs)
        finally:
            self.max_records = saved

    # ------------------------------------------------------------------
    # Server-side JSON response
    # ------------------------------------------------------------------

    def get_server_side_json(self, request, queryset, post_data):
        """Build the DataTables server-side response JSON.

        Parameters
        ----------
        request:
            The Django request object.
        queryset:
            The base queryset returned by ``get_query()``.  It already has
            ``filter``, ``exclude``, ``view_filter``, and ``extra_filters``
            applied, but is not yet sliced.
        post_data:
            ``request.POST`` (or equivalent mapping).
        """
        draw = int(post_data.get('draw', 1))
        start = int(post_data.get('start', 0))
        length = int(post_data.get('length', 25))

        # Cap length to avoid runaway queries.
        max_page = self.max_records or 500
        length = min(length, max_page)

        # Base queryset (view filters only) feeds facet totals.
        base_queryset = queryset
        js_filter_state = self._parse_js_filter_state(post_data)
        # The client asks for facet counts only when the filter/search state
        # changed; paging and sorting draws skip the aggregate queries.
        need_facets = post_data.get('need_facets') == '1' or draw == 1

        # Total records matching the view's base filters (not the user search).
        # Use the fast approximate estimate when requested, otherwise COUNT(*).
        records_total = self._count_total(queryset)

        # Detect whether any search filter is active.
        search_value = post_data.get('search[value]', '').strip()
        n_columns = sum(1 for k in post_data if k.startswith('columns[') and k.endswith('][name]'))
        has_column_search = any(
            post_data.get(f'columns[{i}][search][value]', '').strip()
            for i in range(n_columns)
        )
        search_active = bool(search_value or has_column_search)

        # Apply the global search box value.
        if search_value:
            queryset = self._apply_global_search(queryset, search_value)

        # Apply per-column search values (from column-header input boxes).
        if has_column_search:
            queryset = self._apply_column_searches(queryset, post_data)

        # Apply the js filter selections (pivot/select2/date filter blocks).
        queryset, js_filters_applied = self._apply_js_filters(queryset, js_filter_state)
        filters_active = search_active or js_filters_applied

        # Count after search/filter for the "x of y records" footer.
        # Skip the second COUNT when nothing is being filtered — it equals total.
        records_filtered = queryset.count() if filters_active else records_total

        # Fully-filtered queryset (before ordering/slicing) feeds facet counts.
        filtered_queryset = queryset

        # Apply ordering sent by DataTables (overrides default order_by).
        ordering = self._build_ordering(post_data)
        if ordering:
            queryset = queryset.order_by(*ordering)

        # Slice for the current page.
        page_data = list(queryset[start:start + length])
        data = self.get_table_array(request, page_data)

        result = {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        }
        if need_facets:
            facets = self._build_facets(base_queryset, filtered_queryset)
            if facets:
                result['facets'] = facets
        if self.ajax_commands:
            result['ajax_commands'] = self.ajax_commands

        return json.dumps(result, separators=(',', ':'), default=str)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _count_total(self, queryset):
        """Return the total row count for this queryset.

        When ``approximate_count = True`` and the database is PostgreSQL, uses
        ``pg_class.reltuples`` which is updated by VACUUM/ANALYZE and avoids a
        full sequential scan.  Falls back to a real COUNT on any other database
        or when the queryset has non-trivial WHERE clauses (view-level filters)
        that make the table statistic inaccurate.

        For simple base querysets (no ``self.filter`` / ``self.initial_filter``
        beyond an empty dict) the estimate is accurate enough for display
        purposes at any scale.  Use ``approximate_count = False`` (the default)
        if an exact count is required.
        """
        if not self.approximate_count:
            return queryset.count()

        # Only use the fast path when no view-level filters narrow the rows,
        # otherwise the table statistic would over-count.
        base_filter_empty = (
            not self.filter
            and not self.initial_filter
            and not self.exclude
        )
        if not base_filter_empty:
            return queryset.count()

        from django.db import connection
        if connection.vendor != 'postgresql':
            return queryset.count()

        # Ask PostgreSQL's planner statistics for a fast row estimate.
        table_name = self.model._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT reltuples::bigint FROM pg_class WHERE relname = %s",
                [table_name],
            )
            row = cursor.fetchone()
        if row and row[0] >= 0:
            return int(row[0])
        return queryset.count()

    def _searchable_columns(self):
        """Return columns whose single ORM field can be searched with icontains."""
        cols = []
        for col in self.columns:
            field = col.field
            if field and isinstance(field, str) and 'calculated' not in col.options:
                cols.append(col)
        return cols

    def _apply_global_search(self, queryset, search_value):
        """Filter queryset so that *any* searchable field matches search_value."""
        fields = self.search_fields or [c.field for c in self._searchable_columns()]
        if not fields:
            return queryset
        q = Q()
        for field in fields:
            q |= Q(**{f'{field}__icontains': search_value})
        try:
            return queryset.filter(q)
        except Exception:
            return queryset

    def _apply_column_searches(self, queryset, post_data):
        """Apply per-column search values sent by DataTables."""
        i = 0
        while f'columns[{i}][name]' in post_data:
            col_name = post_data.get(f'columns[{i}][name]', '')
            col_search = post_data.get(f'columns[{i}][search][value]', '').strip()
            if col_search and col_name:
                try:
                    col, _ = self.find_column(col_name)
                    if col.field and isinstance(col.field, str) and 'calculated' not in col.options:
                        queryset = queryset.filter(**{f'{col.field}__icontains': col_search})
                except Exception:
                    pass
            i += 1
        return queryset

    def _build_ordering(self, post_data):
        """Translate DataTables order params into a list of ORM order_by strings."""
        ordering = []
        i = 0
        while f'order[{i}][column]' in post_data:
            col_idx = int(post_data.get(f'order[{i}][column]', 0))
            direction = post_data.get(f'order[{i}][dir]', 'asc')
            if 0 <= col_idx < len(self.columns):
                col = self.columns[col_idx]
                if col.field and isinstance(col.field, str) and 'calculated' not in col.options:
                    prefix = '-' if direction == 'desc' else ''
                    ordering.append(f'{prefix}{col.field}')
            i += 1
        return ordering
