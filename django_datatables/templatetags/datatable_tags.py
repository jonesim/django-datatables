from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
register = template.Library()


@register.simple_tag
def filter_block(datatable, column_no):
    context = {
            'column_no': column_no,
            'filter_title': datatable.columns[column_no].title,
            'html_id': 'filter_' + datatable.columns[column_no].column_name,
            'table': datatable,
    }
    if datatable.columns[column_no].options.get('pivot'):
        return render_to_string('datatables/filter_blocks/pivot_filter.html', context)
    elif datatable.columns[column_no].options.get('total'):
        return render_to_string('datatables/filter_blocks/pivot_totals.html', context)
    elif datatable.columns[column_no].options.get('select2'):
        return render_to_string('datatables/filter_blocks/select2_filter.html', context)
    elif datatable.columns[column_no].options.get('date_filter'):
        return render_to_string('datatables/filter_blocks/date_filter.html', context)
    elif datatable.columns[column_no].options.get('lookup'):
        return render_to_string('datatables/filter_blocks/tag_filter.html', context)
    return ''


@register.simple_tag
def filter_template( template,datatable, title):
    context = {
    #        'column_no': column_no,
            'filter_title': title,
            'html_id': 'filter_' + title.replace(' ', ''),
            'table': datatable,
    }
    return render_to_string(template, context)


@register.inclusion_tag('datatables/filter_blocks/table_search.html')
def table_search(table):
    return {'table': table}


@register.inclusion_tag('datatables/filter_blocks/filter_control.html')
def filter_control(table):
    return {'datatable': table}


@register.simple_tag
def filter_group(datatable):
    filters = []
    for c in range(0, len(datatable.columns)):
        filters.append(filter_block(datatable, c))
    return mark_safe(''.join(filters))
