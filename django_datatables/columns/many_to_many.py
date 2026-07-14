import inspect

from django_datatables.columns import DatatableColumnError
from django_datatables.columns.columns import DatatableColumn



class ManyToManyColumn(DatatableColumn):

    def setup_results(self, request, all_results):
        if self.reverse:
            tags = self.related_model.objects.values_list(self.field_id, 'pk')
        else:
            tags = self.model.objects.values_list('pk', self.field_id)
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

    def row_result(self, data_dict, page_results):
        return page_results['m2m' + self.column_name].get(data_dict['id'], self.blank)

    def get_lookup(self, fields):
        return list(self.related_model.objects.values_list('pk', fields[-1]))

    def __init__(self, *,  html=' %1% ', **kwargs):
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
        self.options['lookup'] = kwargs.pop('lookup', self.get_lookup(fields=fields))
        if 'blank' in kwargs:
            self.options['lookup'].append((-1, kwargs.pop('blank')))
            self.blank = [-1]
        else:
            self.blank = []
        self.options['render'] = [{'var': '%1%', 'html': html, 'function': 'ReplaceLookup'}]
        self.setup_kwargs(kwargs)
