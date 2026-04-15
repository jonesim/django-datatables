import json

from django.db.models import Q

from django_datatables.datatables.datatable_table import DatatableTable


class ServerSideTable(DatatableTable):
    """
    DatatableTable variant that uses DataTables.js server-side processing.

    Each page request is handled by the server: the ORM applies filtering,
    ordering, and slicing rather than loading all rows into the browser.

    Usage
    -----
    Replace ``DatatableTable`` with ``ServerSideTable`` when calling
    ``add_table()`` or set the class on ``table_classes`` in the view:

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

    Limitations
    -----------
    * Client-side JS filters (``add_js_filters``) are not applied because only
      the current page is present in the browser.  Move any required filtering
      to ORM-level ``self.filter`` / ``extra_filters`` / ``view_filter``.
    * ``ColumnTotalsPlugin`` footer sums only cover the current page.
    * The ``reload_table`` ajax command does not recalculate JS filter badges.
    """

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

        # Count after search/filter for the "x of y records" footer.
        # Skip the second COUNT when nothing is being searched — it equals total.
        records_filtered = queryset.count() if search_active else records_total

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
