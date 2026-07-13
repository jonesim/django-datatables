import logging
from datetime import datetime

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Count, Q, Sum

from django_datatables.columns.many_to_many import ManyToManyColumn
from django_datatables.datatables.datatable_error import DatatableError
from django_datatables.filters import DatatableFilter

logger = logging.getLogger(__name__)


class ServerDatatableFilter(DatatableFilter):
    """
    Base class for js filters that work with ``ServerSideTable``.

    Unlike the client-side filters, which filter rows and compute count badges
    in the browser by iterating the full dataset, these filters:

    * apply the user's selection as an ORM WHERE clause (``apply_filter``)
    * compute the ``[filtered, total]`` badge counts with GROUP BY aggregate
      queries (``get_facets``)

    The client sends the current selections in the ``js_filter_state`` POST
    field, keyed by column_name, and receives counts back in the ``facets``
    key of the server-side JSON response.
    """

    # Filters without count badges (e.g. date range) set this False so the
    # table skips the aggregate queries for them.
    has_facets = True

    template_library = dict(
        DatatableFilter.template_library,
        pivot='datatables/filter_blocks/server_pivot_filter.html',
        select2='datatables/filter_blocks/server_select2_filter.html',
        date='datatables/filter_blocks/server_date_filter.html',
        tag='datatables/filter_blocks/server_tag_filter.html',
        totals='datatables/filter_blocks/server_pivot_totals.html',
    )

    def __init__(self, name_or_template, datatable, column=None, max_facet_values=200, **kwargs):
        self._validate_column(column, datatable)
        super().__init__(name_or_template, datatable, column=column, **kwargs)
        self.max_facet_values = max_facet_values
        self._labels = None

    @staticmethod
    def _validate_column(column, datatable):
        if column is None or not isinstance(column.field, str) or 'calculated' in column.options:
            message = (f'Server-side js filter needs a column with a single ORM field, '
                       f'cannot filter {getattr(column, "column_name", None)!r}')
            logger.warning(message)
            raise DatatableError(message)

    @property
    def field(self):
        return self.column.field

    def apply_filter(self, queryset, state):
        return queryset

    def get_facets(self, base_queryset, filtered_queryset):
        return None

    def _label_map(self):
        """Return {db_value: label} for the column, from choices or lookup."""
        if self._labels is None:
            choices = self.column.options.get('choices')
            if not isinstance(choices, dict):
                choices = getattr(self.column, 'choices', None)
            if isinstance(choices, dict):
                self._labels = dict(choices)
            else:
                # lookup entries are [key, label] or [key, [label, colour]]
                lookup = self.column.options.get('lookup') or []
                self._labels = {k: (v[0] if isinstance(v, (list, tuple)) else v) for k, v in lookup}
        return self._labels

    def value_to_key(self, value):
        """Map a database value to the badge/checkbox key shown to the user."""
        if value is None or value == '':
            return 'null'
        label = self._label_map().get(value)
        return str(value) if label is None else str(label)

    def _keys_to_db_values(self, keys):
        """Reverse of value_to_key: labels back to database values.

        One label may map to several database values; keys without a mapping
        pass through unchanged (the ORM coerces string digits for int fields).
        """
        reverse = {}
        for db_value, label in self._label_map().items():
            reverse.setdefault(str(label), []).append(db_value)
        db_values = []
        for key in keys:
            db_values.extend(reverse.get(str(key), [key]))
        return db_values

    def _resolve_model_field(self):
        """Walk the column's ``__`` field path and return the final model field, or None."""
        return self._resolve_field(self.datatable.model, self.field)

    @staticmethod
    def _resolve_field(model, field_path):
        """Walk a ``__`` field path from ``model`` and return the final model field, or None."""
        field = None
        for part in field_path.split('__'):
            if model is None:
                return None
            try:
                field = model._meta.get_field(part)
            except FieldDoesNotExist:
                return None
            model = field.related_model if field.is_relation else None
        return field


class ServerValuesFilter(ServerDatatableFilter):
    """Shared IN-list semantics for the pivot and select2 filters."""

    def apply_filter(self, queryset, state):
        values = state.get('values')
        if values is None:
            return queryset
        keys = [v for v in values if v != 'null']
        q = Q(**{f'{self.field}__in': self._keys_to_db_values(keys)})
        if 'null' in values:
            q |= Q(**{f'{self.field}__isnull': True})
            model_field = self._resolve_model_field()
            if model_field is not None and model_field.get_internal_type() in ('CharField', 'TextField'):
                q |= Q(**{self.field: ''})
        return queryset.filter(q)

    def _facet_annotation(self):
        """Aggregate computed per distinct column value (both GROUP BY queries)."""
        return Count('pk')

    def _facet_value(self, row):
        """Extract the badge number from one GROUP BY result row."""
        return row['_facet_count']

    def get_facets(self, base_queryset, filtered_queryset):
        # Empty order_by() keeps the table's default ordering out of the GROUP BY.
        totals = list(base_queryset.values(self.field).annotate(_facet_count=self._facet_annotation()).order_by())
        if len(totals) > self.max_facet_values:
            logger.warning('Facet filter on %s exceeds max_facet_values (%s distinct values), skipping counts',
                           self.field, len(totals))
            return None
        facets = {}
        for row in totals:
            entry = facets.setdefault(self.value_to_key(row[self.field]), [0, 0])
            entry[1] += self._facet_value(row)
        for row in filtered_queryset.values(self.field).annotate(_facet_count=self._facet_annotation()).order_by():
            entry = facets.setdefault(self.value_to_key(row[self.field]), [0, 0])
            entry[0] += self._facet_value(row)
        return facets


class ServerPivotFilter(ServerValuesFilter):
    pass


class ServerSelect2Filter(ServerValuesFilter):
    pass


class ServerTagFilter(ServerValuesFilter):
    """
    Tag filter for ``ManyToManyColumn`` columns.

    Each tag checkbox cycles through four states: neutral / include (rows
    with *any* included tag, OR) / required (rows with *every* required tag,
    AND) / exclude (rows with *none* of the excluded tags).  The ``null`` key
    matches rows with no tags at all.  Because the M2M join can duplicate
    parent rows the filtered queryset is made ``distinct()`` and facet counts
    use ``Count('pk', distinct=True)``.
    """

    @staticmethod
    def _validate_column(column, datatable):
        if not isinstance(column, ManyToManyColumn):
            message = (f'Server-side tag filter needs a ManyToManyColumn, '
                       f'cannot filter {getattr(column, "column_name", None)!r}')
            logger.warning(message)
            raise DatatableError(message)
        if column.model is not datatable.model:
            message = (f'Server-side tag filter column {column.column_name!r} '
                       f'must belong to the table model {datatable.model.__name__}')
            logger.warning(message)
            raise DatatableError(message)

    @property
    def field(self):
        # ManyToManyColumn sets column.field = None; rebuild the pk path of
        # the relation from the table model.  For a forward M2M field_id is
        # already relative to the table model; for a reverse M2M it is
        # relative to the related model, so recover the reverse lookup name
        # of the connecting M2M field instead.
        column = self.column
        if column.reverse:
            m2m = column.related_model._meta.get_field(column.field_id.split('__')[0])
            return f'{m2m.related_query_name()}__pk'
        return column.field_id

    def _label_map(self):
        labels = super()._label_map()
        # ManyToManyColumn's blank= kwarg appends a synthetic (-1, label)
        # lookup entry; rows with no tags are keyed 'null' server-side.
        for blank_key in self.column.blank or []:
            labels.pop(blank_key, None)
        return labels

    def _keys_to_db_values(self, keys):
        # Keys are labels from the column lookup; the path filters on pk, so
        # a stale or unknown label must match nothing rather than raise from
        # a non-numeric pk lookup.  Tags created after the lookup was built
        # arrive as str(pk) keys and pass through.
        return [v for v in super()._keys_to_db_values(keys) if not isinstance(v, str) or v.isdigit()]

    def apply_filter(self, queryset, state):
        include = [k for k in state.get('include') or [] if isinstance(k, str)]
        required = [k for k in state.get('required') or [] if isinstance(k, str)]
        exclude = [k for k in state.get('exclude') or [] if isinstance(k, str)]
        if not (include or required or exclude):
            return queryset
        path = self.field
        if include:
            q = Q(**{f'{path}__in': self._keys_to_db_values([k for k in include if k != 'null'])})
            if 'null' in include:
                q |= Q(**{f'{path}__isnull': True})
            queryset = queryset.filter(q)
        for key in required:
            # One filter() per tag: chained filters on a multi-valued path
            # each add their own join, giving AND semantics.
            if key == 'null':
                queryset = queryset.filter(**{f'{path}__isnull': True})
            else:
                queryset = queryset.filter(**{f'{path}__in': self._keys_to_db_values([key])})
        if exclude:
            # exclude() on a multi-valued path uses a subquery, dropping rows
            # that have ANY of the excluded tags.
            keys = [k for k in exclude if k != 'null']
            if keys:
                queryset = queryset.exclude(**{f'{path}__in': self._keys_to_db_values(keys)})
            if 'null' in exclude:
                queryset = queryset.exclude(**{f'{path}__isnull': True})
        return queryset.distinct()

    def _facet_annotation(self):
        # The LEFT JOIN multiplies parent rows; count distinct parents so a
        # row with several tags is only counted once per tag group.
        return Count('pk', distinct=True)

    def get_facets(self, base_queryset, filtered_queryset):
        if filtered_queryset is not base_queryset:
            # apply_filter constrains the M2M join, and the facet GROUP BY
            # would reuse it and only see the matching tags.  Re-anchor on
            # the filtered pks so every tag of a matching row is counted.
            filtered_queryset = base_queryset.filter(pk__in=filtered_queryset.values('pk'))
        return super().get_facets(base_queryset, filtered_queryset)


class ServerTotalsFilter(ServerValuesFilter):
    """
    Pivot filter whose badges show ``Sum(sum_column)`` instead of row counts.

    Filtering is identical to the pivot filter; only the facet numbers
    change.  ``sum_column`` must reference a column backed by a plain ORM
    field (annotations cannot be summed with a further aggregate).
    """

    def __init__(self, name_or_template, datatable, column=None, sum_column=None, **kwargs):
        if sum_column is None:
            message = 'Server-side totals filter needs a sum_column= kwarg'
            logger.warning(message)
            raise DatatableError(message)
        # Resolve before super().__init__: DatatableFilter replaces the
        # sum_column kwarg with the column index for template rendering.
        try:
            sum_col = datatable.find_column(sum_column)[0]
        except Exception:
            sum_col = None
        if (sum_col is None or not isinstance(sum_col.field, str) or 'calculated' in sum_col.options
                or self._resolve_field(datatable.model, sum_col.field) is None):
            message = (f'Server-side totals filter sum_column {sum_column!r} '
                       f'must be a column with a plain ORM field')
            logger.warning(message)
            raise DatatableError(message)
        self.sum_field = sum_col.field
        super().__init__(name_or_template, datatable, column=column, sum_column=sum_column, **kwargs)

    def _facet_annotation(self):
        return Sum(self.sum_field)

    def _facet_value(self, row):
        value = row['_facet_count']
        if value is None:
            return 0
        # Decimal sums would be stringified by json.dumps(default=str) and
        # break the client-side number formatting.
        return value if isinstance(value, int) else float(value)


class ServerDateFilter(ServerDatatableFilter):

    has_facets = False

    @staticmethod
    def _parse(date_str):
        try:
            return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
        except (ValueError, AttributeError):
            return None

    def apply_filter(self, queryset, state):
        after = self._parse(state.get('after', ''))
        before = self._parse(state.get('before', ''))
        if after:
            queryset = queryset.filter(**{f'{self.field}__gt': after})
        if before:
            queryset = queryset.filter(**{f'{self.field}__lt': before})
        return queryset
