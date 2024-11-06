import json
from django.template.loader import render_to_string


class ColumnTotals:

    base_template = 'datatables/plugins/column_totals.html'

    @staticmethod
    def footer_cell(data='', css_class=''):
        if css_class:
            css = f' class="{css_class}"'
        else:
            css = ''
        return f'<th{css}>{data}</th>'

    def __init__(self, datatable, column_setup, template=None):
        setup_dict = {}
        column_totals = {}
        if template:
            self.template_name = template
        else:
            self.template_name = self.base_template

        footer = [self.footer_cell() for _c in datatable.columns]
        column_map = {}
        for c, setup in column_setup.items():
            data = ''
            column_no = datatable.find_column(c)[1]
            if setup.get('sum'):
                column_totals[str(column_no)] = 0
                data = f'%{column_no}%'
            if 'text' in setup:
                data = setup['text'].replace(f'%{c}%', f'%{column_no}%')
            footer[column_no] = self.footer_cell(data, setup.get('css_class'))
            setup_dict[str(column_no)] = setup
            column_map[c] = column_no

        html_footer = ''
        for c, f in enumerate(footer):
            if not datatable.columns[c].options.get('hidden'):
                html_footer += f
        html_footer = f'<tr>{html_footer}</tr>'

        self.context = {'datatable': datatable,
                        'footer': html_footer,
                        'totals': json.dumps(column_totals),
                        'column_map': json.dumps(column_map),
                        'setup': json.dumps(setup_dict)}

    def render(self):
        return render_to_string(self.template_name, self.context)
