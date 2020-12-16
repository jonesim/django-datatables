from django.template.loader import render_to_string


class ColourRows:

    def __init__(self, datatable, colour_dict):
        self.colour_dict = colour_dict
        self.datatable = datatable

    def render(self):

        '''
        if 'rowColor' in self.table_options:
            if isinstance(self.table_options['rowColor'], list):
                for rc in self.table_options['rowColor']:
                    if 'colRef' in rc:
                        rc['column'] = self.all_refs().index(rc['colRef'])
            if 'colRef' in self.table_options['rowColor']:
                self.table_options['rowColor']['column'] = self.all_refs().index(self.table_options['rowColor']
                                                                                 ['colRef'])
        '''

        return render_to_string('datatables/plugins/colour_rows.html',
                                {'datatable': self.datatable, 'colour_dict': self.colour_dict})
