from importlib.metadata import PackageNotFoundError

from ajax_helpers.html_include import SourceBase, pip_version

try:
    version = pip_version('django-filtered-datatables')
except PackageNotFoundError:
    version = 'local'


class DataTables(SourceBase):
    cdn_path = 'cdn.datatables.net/v/dt/dt-1.10.18/b-1.5.6/b-html5-1.5.6/rg-1.1.0/rr-1.2.4/'
    filename = 'datatables.min'
    cdn_js_path = ''
    cdn_css_path = ''


class FilteredDataTables(SourceBase):
    static_path = 'django_datatables/'
    js_filename = 'filtered-datatable.js'
    css_filename = 'datatables.css'
    legacy_js = ['runtime.js', 'filtered_datatables_legacy.js']


class Moment(SourceBase):
    cdn_path = 'cdnjs.cloudflare.com/ajax/libs/moment.js/2.8.4/'
    js_filename = 'moment.min.js'
    cdn_js_path = ''


class MomentDatatable(SourceBase):
    cdn_path = 'cdn.datatables.net/plug-ins/1.10.16/sorting/'
    js_filename = 'datetime-moment.js'
    cdn_js_path = ''


packages = {
    'datatable': [DataTables, FilteredDataTables, Moment, MomentDatatable],
}
