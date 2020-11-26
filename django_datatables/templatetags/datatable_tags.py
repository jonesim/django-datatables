from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag
def filter_block(datatable, column_no, column):
    context = {
            'column_no': column_no,
            'column': column,
            'html_id': 'filter_' + column.column_name,
            'table': datatable,
    }
    if column.options.get('pivot'):
        return render_to_string('datatables/filter_blocks/pivot_filter.html', context)
    elif column.options.get('total'):
        return render_to_string('datatables/filter_blocks/pivot_totals.html', context)
    elif column.options.get('select2'):
        return render_to_string('datatables/filter_blocks/select2_filter.html', context)
    elif column.options.get('lookup'):
        return render_to_string('datatables/filter_blocks/tag_filter.html', context)
    return ''


@register.inclusion_tag('datatables/filter_blocks/table_search.html')
def table_search(table):
    return {'table': table}
