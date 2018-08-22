import logging
from flask import current_app
from sqlalchemy import or_


logger = current_app.logger
logger.setLevel(logging.DEBUG)

# Map our filter encodings to sqlalchemy column operators.
# Catalog at http://docs.sqlalchemy.org/en/latest/core/metadata.html#sqlalchemy.schema.Column  # noqa E501
FilterOpMap = {
    'EQUALS': '__eq__',
    'NOT_EQUALS': '__ne__',
    'GREATER_THAN': '__gt__',
    'LESS_THAN': '__lt__'
}  # noqa E503


# rule_set = [
#     (User.name, 'EQUALS', new_person.name),
# ]
# q = session.query(User.name, Address.email).join(Address)
# print(Filter.apply(None, q, filter=(Address.user_id, 'EQUALS', 1)))
# print(CompositeFilter.apply(None, q, filters=rule_set))
class Filter():
    @staticmethod
    def apply(context, query, filter=None):
        if filter:
            field, relation, condition = filter
            # FIXME: preprocess str -> selectable
            return query.filter(
                getattr(field, FilterOpMap[relation])(condition))


class CompositeFilter(Filter):
    @staticmethod
    def apply(context, query, filters=None):
        for f in filters:
            query = Filter.apply(context, query, f)
        return query


class DatasetActorFilterPolicy(CompositeFilter):
    ''' dataset actor data. '''

    @staticmethod
    def apply(context, query, filters=None):
        user = context.user
        if user.tag_object_code in ('1', '2', 'E'):
            columns = context.view.tableDef.columns
            column_names = [column.name for column in columns.values()]
            filters = []

            if ('id_dataset' in column_names and (user.tag_object_code in ('2', 'E'))):  # noqa E501
                from geonature.core.gn_meta.models import TDatasets
                allowed_datasets = TDatasets.get_user_datasets(user)
                if len(allowed_datasets) >= 1:
                    filters.append(columns.id_dataset.in_(tuple(allowed_datasets)))  # noqa E501
                # else:
                #     from pypnusershub.db.tools import InsufficientRightsError
                #     raise InsufficientRightsError
                logger.debug('Allowed datasets: %s', allowed_datasets)

            if 'observers' in column_names:
                filters.append(columns.observers.any(id_role=user.id_role))

            if 'id_digitiser' in column_names:
                filters.append(columns.id_digitiser == user.id_role)

            query = query.filter(or_(*filters))

        return query