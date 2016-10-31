from flask import abort
from flask.ext.sqlalchemy import Pagination
from sqlalchemy import and_, func
from sqlalchemy.orm import aliased
from sqlalchemy.sql import label

from crime_data.common import models
from crime_data.extensions import db

session = db.session


class CdeRefState(models.RefState):
    pass


class CdeRefCity(models.RefCity):
    pass


class CdeRetaOffense(models.RetaOffense):
    pass


class CdeRetaMonthOffenseSubcat(models.RetaMonthOffenseSubcat):
    pass


class CdeRetaOffenseSubcat(models.RetaOffenseSubcat):
    pass


class CdeRefAgency(models.RefAgency):
    pass


class CdeNibrsEthnicity(models.NibrsEthnicity):
    pass


class CdeNibrsVictim(models.NibrsVictim):
    pass


class CdeNibrsOffender(models.NibrsOffender):
    pass


class CdeNibrsMonth(models.NibrsMonth):
    pass


class CdeNibrsOffense(models.NibrsOffense):
    pass


class CdeNibrsLocationType(models.NibrsLocationType):
    pass


class CdeNibrsIncident(models.NibrsIncident):
    '''''
    Extends models.NibrsIncident.
    ''' ''

    @staticmethod
    def __get_fields(agg_fields, fields):
        requested_fields = []
        for field in fields:
            if field in CdeNibrsIncident.get_filter_map():
                requested_fields.append(CdeNibrsIncident.get_filter_map()[
                    field])

        requested_fields += agg_fields
        return requested_fields

    @staticmethod
    def __apply_filters(query, filters):
        for filter, value in filters.items():
            if filter in CdeNibrsIncident.get_filter_map():
                query = query.filter(CdeNibrsIncident.get_filter_map()[filter]
                                     == value)
        return query

    @staticmethod
    def __apply_group_by(query, group_bys):
        for group in group_bys:
            if group in CdeNibrsIncident.get_filter_map():
                query = query.group_by(CdeNibrsIncident.get_filter_map()[
                    group]).order_by(CdeNibrsIncident.get_filter_map()[group])
        return query

    # Maps API filter to DB column name.
    @staticmethod
    def get_filter_map():
        return {'state': CdeRefState.state_abbr,
                'city': CdeRefCity.city_name,
                'month': CdeNibrsMonth.month_num,
                'year': CdeNibrsMonth.data_year,
                'ori': CdeRefAgency.ori,
                'offense_location': CdeNibrsLocationType.location_name,
                'victim_ethnicity':
                CdeNibrsEthnicity.ethnicity_name.label('victim_ethnicity'),
                'offender_ethnicity':
                CdeNibrsEthnicity.ethnicity_name.label('offender_ethnicity')}

    @staticmethod
    def get_nibrs_incident_by_ori(ori=None, filters=None, by=None):
        '''''
        Returns Query for RETA counts by Agency/ORI - Monthly Sums.
        ''' ''

        agg_fields = [
            func.count(CdeNibrsIncident.incident_id).label('incident_count')
        ]

        fields = CdeNibrsIncident.__get_fields(agg_fields, by)

        # Base Query
        query = CdeNibrsIncident.query

        # Get ONE ORI.
        # if ori:
        #     query = query.filter(CdeRefAgency.ori==ori)

        # Apply JOINS.
        query = (query.join(CdeNibrsOffense).join(CdeNibrsLocationType)
                 .outerjoin(CdeNibrsMonth).outerjoin(CdeRefAgency)
                 .outerjoin(CdeRefCity).outerjoin(CdeRefState))

        if 'victim_ethnicity' in by or 'offender_ethnicity' in by:
            if 'victim_ethnicity' in by:
                query = (query.outerjoin(CdeNibrsVictim))
            if 'offender_ethnicity' in by:
                query = (query.outerjoin(CdeNibrsOffender))
            query = query.outerjoin(CdeNibrsEthnicity)

        # Apply field selections.
        query = query.with_entities(*fields)

        # Apply group by.
        query = CdeNibrsIncident.__apply_group_by(query, by)

        # Apply all filters
        query = CdeNibrsIncident.__apply_filters(query, filters)

        return query


class CdeRetaMonth(models.RetaMonth):
    @staticmethod
    def __get_fields(agg_fields, fields):
        requested_fields = []
        for field in fields:
            if field in CdeRetaMonth.get_filter_map():
                requested_fields.append(CdeRetaMonth.get_filter_map()[field])

        requested_fields += agg_fields
        return requested_fields

    @staticmethod
    def __apply_filters(query, filters):
        for filter, value in filters.items():
            if filter in CdeRetaMonth.get_filter_map():
                query = query.filter(CdeRetaMonth.get_filter_map()[filter] ==
                                     value)
        return query

    @staticmethod
    def __apply_group_by(query, group_bys):
        for group in group_bys:
            if group in CdeRetaMonth.get_filter_map():
                query = query.group_by(CdeRetaMonth.get_filter_map()[
                    group]).order_by(CdeRetaMonth.get_filter_map()[group])
        return query

    # Maps API filter to DB column name.
    @staticmethod
    def get_filter_map():
        return {
            'state': CdeRefState.state_abbr,
            'offense': CdeRetaOffense.offense_name,
            'ori': CdeRefAgency.ori,
            'subcategory': CdeRetaOffenseSubcat.offense_subcat_name,
            'agency_name':
            CdeRefAgency.pub_agency_name,  # Assuming Public Agency Name is the best one.
            'city': CdeRefCity.city_name,
            'year': CdeRetaMonth.data_year,
            'month': CdeRetaMonth.month_num
        }

    @staticmethod
    def get_reta_by_ori(ori=None, filters=None, by=None):
        '''''
        Returns Query for RETA counts by Agency/ORI - Monthly Sums.
        ''' ''

        agg_fields = [
            func.sum(CdeRetaMonthOffenseSubcat.actual_count).label(
                'actual_count'),
            func.sum(CdeRetaMonthOffenseSubcat.reported_count).label(
                'reported_count'),
            func.sum(CdeRetaMonthOffenseSubcat.unfounded_count).label(
                'unfounded_count'),
            func.sum(CdeRetaMonthOffenseSubcat.cleared_count).label(
                'cleared_count'),
            func.sum(CdeRetaMonthOffenseSubcat.juvenile_cleared_count).label(
                'juvenile_cleared_count'),
        ]

        fields = CdeRetaMonth.__get_fields(agg_fields, by)

        # Base Query
        query = CdeRetaMonth.query

        # Get ONE ORI.
        # if ori:
        #     query = query.filter(CdeRefAgency.ori==ori)

        # Apply JOINS.
        query = (query.join(CdeRetaMonthOffenseSubcat).outerjoin(CdeRefAgency)
                 .outerjoin(CdeRefCity).outerjoin(CdeRefState)
                 .join(CdeRetaOffenseSubcat).join(CdeRetaOffense))

        # Apply field selections.
        query = query.with_entities(*fields)

        # Apply group by.
        query = CdeRetaMonth.__apply_group_by(query, by)

        # Apply all filters
        query = CdeRetaMonth.__apply_filters(query, filters)

        return query


class TableFamily:
    def _is_string(col):
        return issubclass(col.type.python_type, str)

    def filtered(self, filters):
        qry = self.query()
        for (col_name, comparitor, val) in filters:
            if col_name not in self.map:
                abort(400, 'field {} not found'.format(col_name))
            col = self.map[col_name]
            if _is_string(col):
                col = func.lower(col)
                val = val.lower()
            qry = qry.filter(getattr(col, comparitor)(val))
        return qry

    def _build_map(self):
        self.map = {}
        tables = [self.base_table, ] + self.tables
        for table in tables:
            for (alias, col) in table.map():
                if alias in self.map:
                    print('Column {} already in map'.format(alias))
                else:
                    self.map[alias] = col

    def query(self):

        self._build_map()
        self.print_map()
        qry = self.base_table.table.query
        for table in self.tables:
            if table.join is None:
                qry = qry.join(table.table, isouter=table.outer)
            else:
                qry = qry.join(table.table, table.join, isouter=table.outer)
        return qry

    def print_map(self):
        """
        Quick-and-dirty output into stdout of filter columns for swagger.

        TODO: should be less quick and dirty!
        """

        template = """{{
                      "name": "{name}",
                      "in": "query",
                      "type": "{type}",
                      "required": false
                    }}, """

        types = {int: 'integer', bool: 'boolean', }
        for (name, col) in sorted(self.map.items()):
            sqla_col = list(col.base_columns)[0]
            typ = types.get(sqla_col.type.python_type, 'string')
            print(template.format(name=name, type=typ))


class JoinedTable:

    PREFIX_SEPARATOR = '.'

    def __init__(self, table, outer=True, prefix=None, join=None):
        self.table = table
        self.outer = outer
        self.prefix = prefix
        self.join = join

    def columns(self):
        """
        Build a dictionary mapping column name to column model object
        for all the tables in the table family.
        """
        for attr_name in dir(self.table):
            col = getattr(self.table, attr_name)
            if hasattr(col, 'key') and hasattr(col, 'prop') and hasattr(
                    col, 'base_columns'):
                yield col

    def map(self):
        for col in self.columns():
            if self.prefix:
                alias = '{}{}{}'.format(self.prefix, self.PREFIX_SEPARATOR,
                                        col.key)
            else:
                alias = col.key
            yield (alias, col)


class IncidentTableFamily(TableFamily):

    PREFIX_SEPARATOR = '.'

    base_table = JoinedTable(models.NibrsIncident)

    victim_race = aliased(models.RefRace)
    victim_age = aliased(models.NibrsAge)
    victim_ethnicity = aliased(models.NibrsEthnicity)
    offender_race = aliased(models.RefRace)
    offender_age = aliased(models.NibrsAge)
    offender_ethnicity = aliased(models.NibrsEthnicity)
    arrestee_race = aliased(models.RefRace)
    arrestee_age = aliased(models.NibrsAge)
    arrestee_ethnicity = aliased(models.NibrsEthnicity)

    tables = [
        JoinedTable(models.NibrsOffense),
        JoinedTable(models.NibrsOffenseType),
        JoinedTable(models.RefAgency,
                    outer=False),
        JoinedTable(models.RefAgencyType,
                    outer=False),
        JoinedTable(models.RefState,
                    outer=False),
        JoinedTable(models.RefDivision,
                    outer=False),
        JoinedTable(models.RefRegion,
                    outer=False),
        JoinedTable(models.RefSubmittingAgency,
                    join=(models.RefAgency.agency_id ==
                          models.RefSubmittingAgency.agency_id)),
        JoinedTable(models.RefFieldOffice),
        JoinedTable(models.RefPopulationFamily,
                    join=(models.RefAgency.population_family_id ==
                          models.RefPopulationFamily.population_family_id),
                    outer=False),
        JoinedTable(models.NibrsClearedExcept),
        JoinedTable(models.NibrsOffender),
        JoinedTable(offender_age,
                    join=(models.NibrsOffender.age_id == offender_age.age_id),
                    prefix='offender'),
        JoinedTable(
            offender_race,
            join=(models.NibrsOffender.race_id == offender_race.race_id),
            prefix='offender'),
        JoinedTable(offender_ethnicity,
                    join=(models.NibrsOffender.ethnicity_id ==
                          offender_ethnicity.ethnicity_id),
                    prefix='offender'),
        JoinedTable(victim_age,
                    join=(models.NibrsOffender.age_id == victim_age.age_id),
                    prefix='victim'),
        JoinedTable(victim_race,
                    join=(models.NibrsOffender.race_id == victim_race.race_id),
                    prefix='victim'),
        JoinedTable(victim_ethnicity,
                    join=(models.NibrsOffender.ethnicity_id ==
                          victim_ethnicity.ethnicity_id),
                    prefix='victim'),
        JoinedTable(arrestee_age,
                    join=(models.NibrsOffender.age_id == arrestee_age.age_id),
                    prefix='arrestee'),
        JoinedTable(
            arrestee_race,
            join=(models.NibrsOffender.race_id == arrestee_race.race_id),
            prefix='arrestee'),
        JoinedTable(arrestee_ethnicity,
                    join=(models.NibrsOffender.ethnicity_id ==
                          arrestee_ethnicity.ethnicity_id),
                    prefix='arrestee'),
        JoinedTable(models.NibrsProperty),
        JoinedTable(models.NibrsPropLossType),
        JoinedTable(models.NibrsLocationType,
                    join=(models.NibrsOffense.location_id ==
                          models.NibrsLocationType.location_id)),
    ]


def _is_string(col):
    col0 = list(col.base_columns)[0]
    return issubclass(col0.type.python_type, str)


class FieldNameError(AttributeError):
    pass


class QueryWithAggregates(object):
    def _sql_name(self, readable_name):
        return self.COL_NAME_MAP.get(readable_name, readable_name)

    def _col(self, readable_name, operation=None):
        """Find column named `readable_name` in `self.tables`, return it labelled"""
        for tbl in self.tables:
            try:
                col = getattr(tbl, self._sql_name(readable_name))
            except AttributeError:
                continue
            if operation:
                col = operation(col)
            return label(readable_name, col)
        raise FieldNameError('No field `{}`'.format(readable_name))

    def _apply_filters(self, filters):
        if filters:
            for (col_name, comparitor, value) in filters:
                col = self._col(col_name)
                if _is_string(col):
                    col = func.lower(col)
                    value = value.lower()
                self.qry = self.qry.filter(getattr(col, comparitor)(value))

    def __init__(self, by=None, filters=None):
        try:
            self.qry = self._base_query()
            if by in (['none', None]):
                by = []
            for col_name in by:
                col = self._col(col_name)
                self.qry = self.qry.add_columns(col)
                self.qry = self.qry.group_by(col).order_by(col)
            self._apply_filters(filters)
        except FieldNameError as e:
            abort(400, e)

    def paginate(self, page, per_page):
        paginated = self.qry.limit(per_page).offset((page - 1) * per_page)
        return Pagination(self.qry,
                          page=page,
                          per_page=per_page,
                          total=self.qry.count(),
                          items=paginated)


class RetaQuery(QueryWithAggregates):

    COL_NAME_MAP = {'year': 'data_year',
                    'month': 'month_num',
                    'agency_name': 'ucr_agency_name',
                    'state': 'state_abbr',
                    'city': 'city_name',
                    'tribe': 'tribe_name',
                    'offense': 'offense_name',
                    'offense_subcat': 'offense_subcat_name',
                    'offense_category': 'offense_category_name', }
    tables = [models.RetaMonthOffenseSubcat, models.RetaMonth, CdeRefAgency,
              models.RefCity, models.RefState, models.RefTribe,
              models.RetaOffenseSubcat, models.RetaOffense,
              models.RetaOffenseCategory]
    aggregated = ('actual_count',
                  'reported_count',
                  'unfounded_count',
                  'cleared_count',
                  'juvenile_cleared_count', )

    def _base_query(self, operation=func.sum):
        sum_cols = [self._col(c, operation) for c in self.aggregated]
        qry = db.session.query(sum_cols[0])
        for col in sum_cols[1:]:
            qry = qry.add_columns(col)
        qry = qry.join(models.RetaOffenseSubcat).join(models.RetaOffense).join(
            models.RetaOffenseCategory)
        qry = qry.join(models.RetaMonth).join(models.RefAgency).join(
            models.RefCity,
            isouter=True)
        qry = qry.join(models.RefState,
                       models.RefAgency.state_id == models.RefState.state_id,
                       isouter=True)
        qry = qry.join(models.RefTribe,
                       models.RefAgency.tribe_id == models.RefTribe.tribe_id,
                       isouter=True)
        return qry
