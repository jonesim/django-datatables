from django.template.loader import render_to_string


class Reorder:

    def __init__(self, datatable):
        self.datatable = datatable

    def render(self):
        return render_to_string('datatables/plugins/reorder.html', {'datatable': self.datatable})
