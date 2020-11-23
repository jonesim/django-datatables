from inspect import signature, isclass
from django.core.exceptions import FieldDoesNotExist


class DatatableModel:

    @staticmethod
    def column_info(field_name, **kwargs):
        return

    @staticmethod
    def extract_path(field):
        if '__' in field:
            return field[:field.rfind('__') + 2]
        return ''

    @classmethod
    def get_column_info(cls, model, field_name, **kwargs):
        field_id = field_name.split('__')[-1]
        try:
            config = getattr(model.Datatable, field_id)
            if callable(config):
                if isclass(config):
                    column_setup = config(field_name).column()
                elif len(signature(config).parameters) == 0:
                    column_setup = config()
                else:
                    column_setup = config(field_name)
            else:
                column_setup = config
        except AttributeError:
            column_setup = model.Datatable.column_info(field_id, **kwargs)

        if type(column_setup) == dict:
            column_setup['column_name'] = field_id
        return column_setup

    def table_column_definitions(self):
        pass

    def __init__(self):
        pass

    @staticmethod
    def get_setup_data(model, field):
        """
        Recursive routine to follow foreign keys to get base model for field and check if DataTable class exists
        :param model:
        :param field:
        :return:
        """
        split_field = field.split('__')
        setup = None
        if len(split_field) == 1:
            if hasattr(model, 'Datatable'):
                try:
                    setup = getattr(model.Datatable, field.split('|')[0])
                except AttributeError:
                    setup = model.Datatable.column_info(field)
            try:
                field = model._meta.get_field(field)
            except FieldDoesNotExist:
                field = None
            return model, field, setup
        else:
            next_field = model._meta.get_field(split_field[0])
            if next_field.many_to_one:
                next_model = next_field.foreign_related_fields[0].model
            elif next_field.many_to_many or next_field.one_to_one or next_field.one_to_many:
                next_model = next_field.related_model
            return DatatableModel.get_setup_data(next_model, '__'.join(split_field[1:]))