from inspect import isclass

from django.db import models

from django_datatables.columns import ColumnBase, DateColumn, ChoiceColumn, BooleanColumn, CallableColumn
from django_datatables.datatables.datatable_error import DatatableError
from django_datatables.model_def import DatatableModel


class ColumnInitialisor:

    def __init__(self, start_model, path, field_prefix='', name_prefix='', **kwargs):
        self.start_model = start_model
        self.django_field = None
        self.setup = None
        self.model = None
        if type(path) == tuple:
            kwargs.update(path[1])
            path = path[0]
        self.kwargs = kwargs
        self.columns = []
        self.callable = False
        self.next_prefix = ''
        explicit_name = False
        if isclass(path):
            self.setup = path
            self.next_prefix = field_prefix
            self.kwargs['column_name'] = path.__name__
        elif isinstance(path, ColumnBase):
            self.setup = path
            if not hasattr(path, 'column_name'):
                self.kwargs['column_name'] = type(path).__name__
        elif isinstance(path, str):
            self.path, options = ColumnBase.extract_options(path)
            self.path = field_prefix + self.path
            self.kwargs.update(options)
            if start_model is not None:
                self.model, self.django_field, self.setup = DatatableModel.get_setup_data(start_model, self.path)
            if 'column_name' in self.kwargs:
                explicit_name = True
            else:
                self.kwargs['column_name'] = path

            if '__' in self.path:
                split_path = self.path.split('__')
                self.field = split_path[-1]
                self.next_prefix = '__'.join(split_path[:-1]) + '__'
            else:
                self.field = self.path
            self.callable = callable(getattr(self.model, self.field, None))
        else:
            raise DatatableError('Unknown type in columns ' + str(path))

        if 'column_name' in kwargs and name_prefix and not explicit_name:
            self.kwargs['column_name'] = f'{name_prefix}/{field_prefix}{self.kwargs["column_name"]}'

    def get_columns(self):
        self.kwargs['model'] = self.model
        self.kwargs['model_path'] = self.next_prefix
        if isclass(self.setup):
            self.columns.append(self.setup(**self.kwargs))
        elif isinstance(self.setup, ColumnBase):
            if self.setup.initialised:
                if 'table' in self.kwargs:
                    self.setup.table = self.kwargs['table']
                self.columns.append(self.setup)
            else:
                self.columns.append(self.setup.get_class_instance(**self.kwargs))
        elif isinstance(self.setup, list):
            del self.kwargs['column_name']
            for c in self.setup:
                new_column_initialisor_cls = type(self)  # calls it's self (ColumnInitialisor)
                self.columns += new_column_initialisor_cls(start_model=self.start_model,
                                                           path=c,
                                                           field_prefix=self.next_prefix,
                                                           name_prefix=self.field,
                                                           **self.kwargs).get_columns()
        elif self.callable:
            if self.setup is None:
                self.setup = {}
            self.columns.append(CallableColumn(field=self.field, **self.kwargs, **self.setup))
        else:
            self.kwargs['field'] = self.field
            if isinstance(self.setup, dict):
                self.kwargs.update(self.setup)
            if self.django_field:
                self.add_django_field_column()
            else:
                self.columns.append(ColumnBase(**self.kwargs))
        return self.columns

    def add_django_field_column(self):
        if 'title' not in self.kwargs:
            self.kwargs['title'] = self.django_field.verbose_name.title()
        if isinstance(self.django_field, (models.DateField, models.DateTimeField)):
            self.columns.append(DateColumn(**self.kwargs))
        elif (isinstance(self.django_field,
                         (models.IntegerField, models.PositiveSmallIntegerField, models.PositiveIntegerField))
              and self.django_field.choices is not None and len(self.django_field.choices) > 0):
            self.columns.append(ChoiceColumn(choices=self.django_field.choices, **self.kwargs))
        elif isinstance(self.django_field, models.BooleanField):
            self.columns.append(BooleanColumn(**self.kwargs))
        else:
            self.columns.append(ColumnBase(**self.kwargs))
