import json

from datatable_examples import models
from datatable_examples.views.base import ManualPage
from django_datatables.columns import ColumnBase, DatatableColumn, DateColumn, ManyToManyColumn
from django_datatables.datatables import DatatableView
from django_datatables.helpers import render_replace, row_button


class NumberEdit(DatatableColumn):
    """A column rendered as a number input; the value posts back on blur."""

    def row_result(self, data_dict, _page_results):
        return ('<form><input style="text-align:right" type="number" name="count" '
                'onblur=django_datatables.b_r(this) ></form>')


class InlineEditing(ManualPage, DatatableView):
    model = models.Person
    page_title = 'Inline Editing'
    ajax_commands = ['row', 'column']
    code_examples = ['setup_table', 'row_column']

    @staticmethod
    def setup_table(table):
        table.edit_fields = ['first_name', 'title', 'company__name']
        table.edit_options = {'company__name': {'select2': True}}
        table.add_columns(
            'id',
            'first_name',
            'title_model',
            ('company__name', {'title': 'Company Name'}),
            DateColumn('date_entered', column_name='Date'),
            NumberEdit(column_name='number_edit', title='Number input'),
            'surname',
        )

    def row_column(self, row_data, inputs, **kwargs):
        row = json.loads(row_data)
        return self.command_response('message', text=f'Row id {row[0]} sent {dict(inputs)}')

    def add_to_context(self, **kwargs):
        return {'description': (
            'Fields listed in <code>edit_fields</code> become editable in place — double-click a first '
            'name, title, or company. A <code>ChoiceColumn</code> edits with a dropdown of its choices, '
            'and <code>edit_options</code> upgrades a field to a select2 search. The save posts back '
            'through the view\'s <code>row_edit</code> handler and the row refreshes. '
            'The last column is a custom column that renders an <code>&lt;input&gt;</code> in every '
            'row; on blur <code>django_datatables.b_r(this)</code> posts the value and the row data to '
            'the view\'s <code>row_column</code> method.'
        )}


class RowButtons(ManualPage, DatatableView):
    model = models.Company
    page_title = 'Row Buttons'
    ajax_commands = ['row']
    code_examples = ['setup_table', 'row_toggle_tag', 'row_delete']

    def row_delete(self, **kwargs):
        # Could delete from the database here, but for the demo only the displayed row is removed
        return self.command_response('delete_row', row_no=kwargs['row_no'], table_id=kwargs['table_id'])

    def row_toggle_tag(self, **kwargs):
        row_data = json.loads(kwargs['row_data'])
        table = self.tables[kwargs['table_id']]
        self.setup_tables(table_id=table.table_id)

        company = models.Company.objects.get(id=row_data[0])
        tag = models.Tags.objects.get(id=1)
        if tag in company.tags_set.all():
            company.tags_set.remove(tag)
        else:
            company.tags_set.add(tag)
        return table.refresh_row(self.request, kwargs['row_no'])

    @staticmethod
    def setup_table(table):
        table.add_columns(
            'id',
            ColumnBase(column_name='idx', field=['id', 'name'], title='Rendered with helper', render=[
                render_replace(html='<b>%1%</b>&nbsp;<i>%2%</i>', column='idx:0'),
                render_replace(var='%2%', column='idx:1'),
            ]),
            ColumnBase(column_name='BasicButton', render=[row_button('toggle_tag', 'toggle TAG1')]),
            ColumnBase(column_name='FormattedButton', render=[row_button('toggle_tag', 'toggle TAG1',
                                                              button_classes='btn %1% btn-sm',
                                                              var='%1%',
                                                              value=1,
                                                              column='CompanyTags',
                                                              choices=['btn-success', ''],
                                                              function='ValueInColumn')]),
            ColumnBase(column_name='Delete', render=[row_button('delete', 'Delete Row')]),
            ManyToManyColumn(column_name='CompanyTags', field='tags__tag', model=models.Company,
                             html='<span class="badge badge-primary"> %1% </span>'),
        )
        table.ajax_data = False

    def add_to_context(self, **kwargs):
        return {'description': (
            'The <code>row_button</code> helper renders a button in every row that posts the row back '
            'to a <code>row_&lt;name&gt;</code> method on the view. <i>toggle TAG1</i> adds or removes '
            'a tag and refreshes just that row with <code>table.refresh_row</code>; the formatted '
            'variant styles itself green when the tag is present by checking the '
            '<code>CompanyTags</code> column with the <code>ValueInColumn</code> function. '
            '<i>Delete Row</i> responds with the <code>delete_row</code> command, which removes the '
            'row client-side.'
        )}
