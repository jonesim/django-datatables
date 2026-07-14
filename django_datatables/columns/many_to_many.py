import inspect

from django.db import ProgrammingError, OperationalError

from django_datatables.columns import DatatableColumnError
from django_datatables.columns.columns import DatatableColumn


class ManyToManyColumn(DatatableColumn):

    def refresh_lookup(self):
        # The lookup (pk -> name) is built in __init__ at startup, but a column instance is a
        # singleton reused for the life of the process, so related rows added later would be missing.
        # Rebuild it from the database each time the lookup is consumed. A lookup passed in
        # explicitly is treated as static and never refreshed.
        if not self._refresh_lookup:
            return
        lookup = self.get_lookup(fields=[self._lookup_name_field])
        self.options['lookup_dict'] = dict(lookup)
        if self._lookup_has_blank:
            lookup = lookup + [(-1, self._lookup_blank)]
        self.options['lookup'] = lookup

    def style(self):
        # style() is called per page-render immediately before options are serialised to the
        # client, so refresh here to send an up-to-date lookup to the browser.
        self.refresh_lookup()
        return super().style()

    def setup_results(self, request, all_results):
        # Keep the server-side lookup_dict current for the Excel/clipboard export path.
        self.refresh_lookup()
        query = getattr(self.related_model if self.reverse else self.model, self.query_manager)
        values_fields = (self.field_id, 'pk') if self.reverse else ('pk', self.field_id)
        tags = query.values_list(*values_fields)
        tags = tags.filter(**{self.field_id + '__isnull': False})
        if self.kwargs.get('exclude'):
            tags = tags.exclude(**self.kwargs['exclude'])
        if self.kwargs.get('filter'):
            tags = tags.filter(**self.kwargs['filter'])
        tags = tags.distinct()
        tag_dict = {}
        for t in tags:
            tag_dict.setdefault(t[0], []).append(t[1])
        all_results['m2m' + self.column_name] = tag_dict
        if self.sort_results:
            for v in all_results['m2m' + self.column_name].values():
                v.sort()

    def row_result(self, data_dict, page_results):
        return page_results['m2m' + self.column_name].get(data_dict[self.field], self.blank)

    def get_lookup(self, fields):
        try:
            return list(self.related_model.objects.values_list('pk', fields[-1]))
        except (ProgrammingError, OperationalError):
            return []

    def __init__(self, *, html=' %1% ', data_dict_key='id', query_manager='objects', sort_results=False, **kwargs):
        if not self.initialise(locals()):
            return
        super().__init__(**self.kwargs)
        fields = self.field.split('__')
        if not inspect.isclass(self.model):
            raise DatatableColumnError('ManyToManyColumn must have model set')
        # noinspection PyProtectedMember
        connecting_field = self.model._meta.get_field(fields[-2])
        self.related_model = connecting_field.related_model
        if hasattr(connecting_field, 'field'):
            self.field_id = connecting_field.field.attname + '__pk'
            self.reverse = True
        else:
            self.field_id = fields[-2] + '__pk'
            self.reverse = False
        self.field = None
        self.query_manager = query_manager
        self.sort_results = sort_results
        # Remember what's needed to rebuild the lookup per render (see refresh_lookup). A lookup
        # passed in explicitly is static and must not be refreshed from the database.
        self._lookup_name_field = fields[-1]
        self._refresh_lookup = 'lookup' not in kwargs
        self._lookup_has_blank = 'blank' in kwargs
        self._lookup_blank = kwargs.get('blank')
        self.options['lookup'] = kwargs.pop('lookup', self.get_lookup(fields=fields))
        self.options['lookup_dict'] = dict(self.options['lookup'])
        if 'blank' in kwargs:
            self.options['lookup'].append((-1, kwargs.pop('blank')))
            self.blank = [-1]
        else:
            self.blank = []
        self.options['render'] = [{'var': '%1%', 'html': html, 'function': 'ReplaceLookup'}]
        self.setup_kwargs(kwargs)
        if len(fields) > 2:
            self.field = '__'.join(fields[:-2]) + '__pk'
        else:
            self.field = data_dict_key

    def excel(self, value):
        return ', '.join(str(self.options['lookup_dict'].get(v, '')) for v in value)
