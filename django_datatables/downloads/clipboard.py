import json

from ajax_helpers.utils import ajax_command
from django_menus.menu import MenuItem

from django_datatables.helpers import add_filters


class ClipboardCopy:
    tables: dict

    ajax_commands = ['column']
    download_id = 'id'

    def clipboard_menu_item(self, table_name=None):
        if table_name is None:
            table_name = list(self.tables.keys())[0]
        return MenuItem(ajax_command('send_column', method='get_clipboard', column=self.download_id,
                                     table_id=table_name),
                        'Copy to Clipboard', font_awesome='fas fa-copy', link_type=MenuItem.AJAX_COMMAND)

    def copy_clipboard(self, table):
        excel_function = [count for count, c in enumerate(table.columns) if hasattr(c, 'excel')]
        rows = ['\t'.join([str(c.title) for c in table.columns if not c.options.get('hidden')])]
        results = table.get_table_array(self.request, table.table_data if table.table_data
                                        else self.get_table_query(table))
        for r in results:
            for f in excel_function:
                r[f] = table.columns[f].excel(r[f])
            rows.append('\t'.join([str(x) if x else '' for c, x in enumerate(r)
                   if not table.columns[c].options.get('hidden')]))
        self.add_command('clipboard', text='\n'.join(rows))
        return self.command_response('message', text='Table copied to clipboard')

    def column_get_clipboard(self, **kwargs):
        column_data = json.loads(kwargs['column_data'])
        table = self.tables[kwargs['table_id']]
        self.setup_tables(table_id=table.table_id)
        table.filter = add_filters(table.filter, {f'{self.download_id}__in': column_data})
        return self.copy_clipboard(table)
