from show_src_code.apps import PypiAppConfig


class DatatableExampleConfig(PypiAppConfig):
    default = True
    name = 'datatable_examples'
    pypi = 'django-filtered-datatables'
    urls = 'datatable_examples.urls'
