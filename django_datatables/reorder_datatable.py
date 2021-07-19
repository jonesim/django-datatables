from django_datatables.datatables import DatatableView, DatatableTable


def reorder(model, order_field, sort_data):
    current_sort = dict(model.objects.values_list('pk', order_field))
    for s in sort_data:
        if current_sort[s[1]] != s[0]:
            o = model.objects.get(id=s[1])
            setattr(o, order_field, s[0])
            o.save()


class OrderedDatatable(DatatableTable):

    def __init__(self, *args, order_field=None, **kwargs):
        self.order_field = order_field
        table_options = {
            'dom': 't',
            'no_col_search': True,
            'no_footer': True,
            'pageLength': 400,
            'stateSave': False,
            'rowReorder': True,
        }
        if not kwargs:
            kwargs = {}
        elif kwargs.get('table_options') is None:
            kwargs['table_options'] = table_options
        else:
            kwargs['table_options'] = table_options.update(kwargs.get('table_options', {}))
        super().__init__(*args, **kwargs)
        self.table_classes = ['display', 'compact', 'smalltext', 'table-sm', 'table']
        self.add_columns(
            '._index',
            '.pk', ('_handle',  {'title': '', 'column_defs': {'width': '30px', 'className': 'button-cell'}}),
        )

    def get_query(self, **kwargs):
        data = super().get_query(**kwargs).order_by(self.order_field)
        for i, d in enumerate(data):
            d['index'] = i
            d['handle'] = '<i class="btn btn-sm btn-outline-secondary fas fa-arrows-alt-v"></i>'
        return data

    def col_def_str(self):
        for c in self.columns:
            c.column_defs['orderable'] = False
        return super().col_def_str()


class ReorderDatatableView(DatatableView):

    order_field: str
    ajax_commands = ['datatable']

    def add_sortable_table(self, table_id, order_field, **kwargs):
        self.tables[table_id] = OrderedDatatable(
            table_id, table_options=self.table_options, order_field=order_field, **kwargs)

    def datatable_sort(self, **kwargs):
        table = self.tables[kwargs['table_id']]
        reorder(table.model, table.order_field, kwargs['sort'])
        # noinspection PyUnresolvedReferences
        return self.command_response('reload_table', table_id=kwargs['table_id'])

    def add_tables(self):
        self.add_sortable_table(type(self).__name__.lower(), model=self.model, order_field=self.order_field)
