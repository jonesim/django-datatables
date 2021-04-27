from django.template.loader import render_to_string


class ColourRows:

    def __init__(self, datatable, colour_dict):
        if isinstance(colour_dict, list):
            self.colour_dict = colour_dict
        else:
            self.colour_dict = [colour_dict]
        for c in self.colour_dict:
            c['column'] = datatable.find_column(c['column'])[1]
        self.datatable = datatable

    def render(self):
        return render_to_string('datatables/plugins/colour_rows.html',
                                {'datatable': self.datatable, 'colour_dict': self.colour_dict})
