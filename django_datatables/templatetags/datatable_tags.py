from django import template
from django.utils.safestring import mark_safe
from django_datatables.filters import DatatableFilter
register = template.Library()


@register.simple_tag
def filter_template(name_or_template, datatable, **kwargs):
    return DatatableFilter(name_or_template, datatable, **kwargs).render()


@register.inclusion_tag('datatables/filter_blocks/table_search.html')
def table_search(table):
    return {'table': table}


@register.inclusion_tag('datatables/filter_blocks/filter_control.html')
def filter_control(table):
    return {'datatable': table}


@register.simple_tag
def filter_group(datatable):
    filters = []
    for f in datatable.js_filter_list:
        filters.append(f.render())
    return mark_safe(''.join(filters))
