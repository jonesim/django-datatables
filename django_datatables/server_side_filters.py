import logging
from datetime import datetime

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Count, Q

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
    )

    def __init__(self, name_or_template, datatable, column=None, max_facet_values=200, **kwargs):
        if column is None or not isinstance(column.field, str) or 'calculated' in column.options:
            message = (f'Server-side js filter needs a column with a single ORM field, '
                       f'cannot filter {getattr(column, "column_name", None)!r}')
            logger.warning(message)
            raise DatatableError(message)
        super().__init__(name_or_template, datatable, column=column, **kwargs)
        self.max_facet_values = max_facet_values
        self._labels = None

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
        """Walk the ``__`` field path and return the final model field, or None."""
        model = self.datatable.model
        field = None
        for part in self.field.split('__'):
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

    def get_facets(self, base_queryset, filtered_queryset):
        # Empty order_by() keeps the table's default ordering out of the GROUP BY.
        totals = list(base_queryset.values(self.field).annotate(_facet_count=Count('pk')).order_by())
        if len(totals) > self.max_facet_values:
            logger.warning('Facet filter on %s exceeds max_facet_values (%s distinct values), skipping counts',
                           self.field, len(totals))
            return None
        facets = {}
        for row in totals:
            entry = facets.setdefault(self.value_to_key(row[self.field]), [0, 0])
            entry[1] += row['_facet_count']
        for row in filtered_queryset.values(self.field).annotate(_facet_count=Count('pk')).order_by():
            entry = facets.setdefault(self.value_to_key(row[self.field]), [0, 0])
            entry[0] += row['_facet_count']
        return facets


class ServerPivotFilter(ServerValuesFilter):
    pass


class ServerSelect2Filter(ServerValuesFilter):
    pass


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
