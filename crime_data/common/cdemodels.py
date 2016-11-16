from flask import abort
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import aliased
from sqlalchemy.sql import label

from crime_data.common import models
from crime_data.common.base import QueryTraits
from crime_data.extensions import db

session = db.session


class CdeRefState(models.RefState):
    pass


class CdeNibrsAge(models.NibrsAge):
    pass


class CdeNibrsOffenseType(models.NibrsOffenseType):
    pass


class CdeNibrsWeapon(models.NibrsWeapon):
    pass


class CdeNibrsWeaponType(models.NibrsWeaponType):
    pass


class CdeRefRace(models.RefRace):
    pass


class CdeRefCity(models.RefCity):
    pass


class CdeRetaMonthOffenseSubcat(models.RetaMonthOffenseSubcat):
    pass


class CdeRefAgency(models.RefAgency, QueryTraits):
    @staticmethod
    def get_filter_map():
        return {'state': CdeRefState.state_abbr.label('state'),
                'city': CdeRefCity.city_name.label('city')}

    def get(ori=None, filters=None, args=None):
        # Base Query
        query = CdeRefAgency.query

        # Get ONE ORI.
        if ori:
            query = query.filter(CdeRefAgency.ori == ori)

        # Apply all filters
        query = CdeRefAgency.apply_filters(query, filters, args)

        return query

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


class CdeNibrsIncident(models.NibrsIncident, QueryTraits):

    offender_ethnicity = aliased(CdeNibrsEthnicity, name='offender_ethnicity')
    victim_ethnicity = aliased(CdeNibrsEthnicity, name='victim_ethnicity')
    victim_race = aliased(CdeRefRace, name='victim_race')
    victim_age = aliased(CdeNibrsAge, name='victim_age')
    offender_race = aliased(CdeRefRace, name='offender_race')
    offender_age = aliased(CdeNibrsAge, name='offender_age')
    arrestee_race = aliased(CdeRefRace, name='arrestee_race')
    arrestee_age = aliased(CdeNibrsAge, name='arrestee_age')
    arrestee_ethnicity = aliased(CdeNibrsEthnicity, name='arrestee_ethnicity')
    '''''
    Extends models.NibrsIncident.
    ''' ''

    # Maps API filter to DB column name.
    @staticmethod
    def get_filter_map():
        return {
            'state': CdeRefState.state_abbr.label('state'),
            'city': CdeRefCity.city_name.label('city'),
            'month': CdeNibrsMonth.month_num,
            'year': CdeNibrsMonth.data_year,
            'ori': CdeRefAgency.ori,
            'offense': CdeNibrsOffenseType.offense_name,
            'offense.location': CdeNibrsLocationType.location_name,
            'victim.ethnicity':
            CdeNibrsIncident.victim_ethnicity.ethnicity_name.label(
                'victim.ethnicity'),
            'offender.ethnicity':
            CdeNibrsIncident.offender_ethnicity.ethnicity_name.label(
                'offender.ethnicity'),
            'victim.race_code':
            CdeNibrsIncident.victim_race.race_code.label('victim.race_code'),
            'victim.age_code':
            CdeNibrsIncident.victim_age.age_code.label('victim.age_code'),
            'offender.race_code':
            CdeNibrsIncident.offender_race.race_code.label(
                'offender.race_code'),
            'offender.age_code':
            CdeNibrsIncident.offender_age.age_code.label('offender.age_code'),
            'arrestee.race_code':
            CdeNibrsIncident.arrestee_race.race_code.label(
                'arestee.race_code'),
            'arrestee.age_code':
            CdeNibrsIncident.arrestee_age.age_code.label('arestee.age_code'),
            'arrestee.ethnicity':
            CdeNibrsIncident.arrestee_ethnicity.ethnicity_name.label(
                'arrestee.ethnicity'),
        }

    @staticmethod
    def get_nibrs_incident_by_ori(ori=None, filters=None, by=None, args=None):
        '''''
        Returns Query for RETA counts by Agency/ORI - Monthly Sums.
        ''' ''

        agg_fields = [
            func.count(CdeNibrsIncident.incident_id).label('incident_count'),
        ]

        fields = CdeNibrsIncident.get_fields(agg_fields, by)

        # Always group by ORI
        fields.append(CdeRefAgency.ori)
        by.append('ori')

        # Base Query
        query = CdeNibrsIncident.query

        # Apply JOINS.
        query = (
            query.join(CdeNibrsOffense).join(CdeNibrsLocationType)
            .outerjoin(CdeNibrsOffenseType)
            .outerjoin(CdeNibrsMonth).outerjoin(CdeRefAgency)
            .outerjoin(CdeRefCity).outerjoin(CdeRefState)
            .outerjoin(CdeNibrsOffender).outerjoin(CdeNibrsWeapon)
            .outerjoin(CdeNibrsWeaponType).outerjoin(models.NibrsAge)
            .outerjoin(
                CdeNibrsIncident.arrestee_age,
                CdeNibrsAge.age_id == CdeNibrsIncident.arrestee_age.age_id)
            .outerjoin(
                CdeNibrsIncident.victim_age,
                CdeNibrsAge.age_id == CdeNibrsIncident.victim_age.age_id)
            .outerjoin(
                CdeNibrsIncident.offender_age,
                CdeNibrsAge.age_id == CdeNibrsIncident.offender_age.age_id)
            .outerjoin(models.RefRace).outerjoin(
                CdeNibrsIncident.arrestee_race,
                CdeRefRace.race_id == CdeNibrsIncident.arrestee_race.race_id)
            .outerjoin(
                CdeNibrsIncident.victim_race,
                CdeRefRace.race_id == CdeNibrsIncident.victim_race.race_id)
            .outerjoin(
                CdeNibrsIncident.offender_race,
                CdeRefRace.race_id == CdeNibrsIncident.offender_race.race_id)
            .outerjoin(CdeNibrsEthnicity).outerjoin(
                CdeNibrsIncident.victim_ethnicity,
                CdeNibrsOffender.ethnicity_id ==
                CdeNibrsIncident.victim_ethnicity.ethnicity_id).outerjoin(
                    CdeNibrsIncident.offender_ethnicity,
                    CdeNibrsOffender.ethnicity_id ==
                    CdeNibrsIncident.offender_ethnicity.ethnicity_id))

        # Apply field selections.
        query = query.with_entities(*fields)

        # Apply group by.
        query = CdeNibrsIncident.apply_group_by(query, by)

        # Apply all filters
        query = CdeNibrsIncident.apply_filters(query, filters, args)

        return query


class CdeRetaMonth(models.RetaMonth, QueryTraits):

    # Maps API filter to DB column name.
    @staticmethod
    def get_filter_map():
        return {
            'state': CdeRefState.state_abbr.label('state'),
            'offense': CdeRetaOffense.offense_name,
            'ori': CdeRefAgency.ori,
            'subcategory': CdeRetaOffenseSubcat.offense_subcat_name,
            'agency_name':
            CdeRefAgency.pub_agency_name,  # Assuming Public Agency Name is the best one.
            'city': CdeRefCity.city_name.label('city'),
            'year': CdeRetaMonth.data_year,
            'month': CdeRetaMonth.month_num
        }

    @staticmethod
    def get_reta_by_ori(ori=None, filters=None, by=None, args=None):
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

        fields = CdeRetaMonth.get_fields(agg_fields, by)

        # Base Query
        query = CdeRetaMonth.query

        # Apply JOINS.
        query = (query.join(CdeRetaMonthOffenseSubcat).outerjoin(CdeRefAgency)
                 .outerjoin(CdeRefCity).outerjoin(CdeRefState)
                 .join(CdeRetaOffenseSubcat).join(CdeRetaOffense))

        # Apply field selections.
        query = query.with_entities(*fields)

        # Apply group by.
        query = CdeRetaMonth.apply_group_by(query, by)

        # Apply all filters
        query = CdeRetaMonth.apply_filters(query, filters, args)

        return query


class CdeCrimeType(models.CrimeType):
    pass


class CdeRetaOffenseCategory(models.RetaOffenseCategory):

    crime_type = db.relationship(CdeCrimeType, backref='categories')


class CdeRetaOffense(models.RetaOffense):

    category = db.relationship(CdeRetaOffenseCategory, backref='offenses')


class CdeRetaOffenseSubcat(models.RetaOffenseSubcat):

    offense = db.relationship(CdeRetaOffense, backref='subcategories')


class CdeOffenseClassification(models.OffenseClassification):

    offense = db.relationship(CdeRetaOffense, backref='classifications')


class JoinedTable:

    PREFIX_SEPARATOR = '.'

    def __init__(self, table, prefix=None, join=None, parent=None):
        self.table = table
        self.prefix = prefix
        self.join = join
        self.parent = parent

    def columns(self):
        """Yield all this model's columns."""

        if hasattr(self.table, '_aliased_insp'):
            column_source = self.table._aliased_insp.class_
            # TODO: Relying on underscores is scary.
        else:
            column_source = self.table
        for attr_name in dir(column_source):
            # distinguish actual columns from other model attributes
            try:
                col = getattr(self.table, attr_name)
                if hasattr(col, 'key') and hasattr(col, 'prop') and hasattr(
                        col, 'base_columns'):
                    yield col
            except ArgumentError:
                pass

    def map(self):
        """Yield (column_name, column) for this table."""

        for col in self.columns():
            column_names = [col.key, ]
            if col.key in SIMPLIFIED_COLUMN_NAMES:
                column_names.append(SIMPLIFIED_COLUMN_NAMES[col.key])
            for column_name in column_names:
                if self.prefix:
                    alias = '{}{}{}'.format(self.prefix, self.PREFIX_SEPARATOR,
                                            column_name)
                else:
                    alias = column_name
                yield (alias, col)


class TableFamily:
    def __init__(self):
        self._map = {}

    @property
    def map(self):
        if not self._map:
            self._build_map()
        return self._map

    def base_query(self):
        return db.session.query(self.base_table.table)

    def _col(self, col_name):
        if col_name not in self.map:
            abort(400, 'field {} not found'.format(col_name))
        return self.map[col_name]

    def filtered(self, filters):
        qry = self.base_query()
        self.joined = {self.base_table,
                       }  # Messy way to track what has been joined
        for (col_name, comparitor, values) in filters:
            (joined_tbl, col) = self._col(col_name)
            qry = self.join(qry, joined_tbl)
            if _is_string(col):
                col = func.lower(col)
                values = [val.lower() for val in values]
            operation = getattr(col, comparitor)
            qry = qry.filter(or_(operation(v) for v in values))
        return qry

    def join(self, qry, table):
        """Joins `table` (JoinedTable instance) if not already present"""
        if table not in self.joined:
            if table.parent:
                qry = self.join(qry, table.parent)
            if table.join is None:
                qry = qry.outerjoin(table.table)
            else:
                qry = qry.outerjoin(table.table, table.join)
            self.joined.add(table)
        return qry

    def group_by(self, qry, group_columns):
        for col_name in group_columns:
            (table, col) = self._col(col_name)
            qry = self.join(qry, table)
            if col_name in UNDERLYING_COLUMN_NAMES:
                col = label(col_name, col)
            elif col_name in SIMPLIFIED_COLUMN_NAMES:
                col = label(SIMPLIFIED_COLUMN_NAMES[col_name], col)
            qry = qry.add_columns(col)
            qry = qry.group_by(col).order_by(col)
        return qry

    def _build_map(self):
        """Create a record of SQLAlchemy columns by column name."""
        self._map = {}
        tables = [self.base_table, ] + self.tables
        for table in tables:
            for (alias, col) in table.map():
                # this alias includes the baked-in table name
                if alias in self._map:
                    print('Column {} already in map'.format(alias))
                else:
                    self._map[alias] = (table, col)
        # self.print_map() # - uncomment to generate JSON

    def query(self):
        self._build_map()
        # self.print_map() # - uncomment to generate JSON
        qry = self.base_query()
        for table in self.tables:
            if table.join is None:
                qry = qry.outerjoin(table.table)
            else:
                qry = qry.outerjoin(table.table, table.join)
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

        print('\n\nmappings for {}\n\n'.format(self))
        types = {int: 'integer', bool: 'boolean', }
        for (name, (table, col)) in sorted(self.map.items()):
            sqla_col = list(col.base_columns)[0]
            typ = types.get(sqla_col.type.python_type, 'string')
            print(template.format(name=name, type=typ))

    @classmethod
    def agency_tables(cls, parent):
        agency_tables = []
        _agency = JoinedTable(models.RefAgency, parent=parent)
        agency_tables.append(_agency)
        agency_tables.append(JoinedTable(models.RefAgencyType,
                                         parent=_agency)),
        _state = JoinedTable(models.RefState, parent=_agency)
        agency_tables.append(_state),
        agency_tables.append(JoinedTable(models.RefCity, parent=_agency))
        _division = JoinedTable(models.RefDivision, parent=_state)
        agency_tables.append(_division)
        agency_tables.append(JoinedTable(models.RefRegion, parent=_division))
        agency_tables.append(JoinedTable(models.RefSubmittingAgency, # prefix?
                        join=(models.RefAgency.agency_id ==
                              models.RefSubmittingAgency.agency_id)))
        agency_tables.append(JoinedTable(models.RefFieldOffice,
                                         parent=_agency))
        agency_tables.append(JoinedTable(
            models.RefPopulationFamily,
            parent=_agency,
            join=(models.RefAgency.population_family_id ==
                  models.RefPopulationFamily.population_family_id), ))
        return agency_tables


UNDERLYING_COLUMN_NAMES = {'year': 'data_year',
                           'month': 'month_num',
                           'agency_name': 'ucr_agency_name',
                           'state': 'state_abbr',
                           'city': 'city_name',
                           'tribe': 'tribe_name',
                           'offense': 'offense_name',
                           'offense_subcat': 'offense_subcat_name',
                           'offense_category': 'offense_category_name', }

SIMPLIFIED_COLUMN_NAMES = {v: k for (k, v) in UNDERLYING_COLUMN_NAMES.items()}


class IncidentTableFamily(TableFamily):

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

    def base_query(self):
        result = db.session.query(models.NibrsIncident.incident_id)
        return result

    tables = []
    offense = JoinedTable(models.NibrsOffense)
    tables.append(offense)
    tables.append(JoinedTable(models.NibrsOffenseType, parent=offense)),
    tables.extend(TableFamily.agency_tables(None))
    tables.append(JoinedTable(models.NibrsClearedExcept))
    offender = JoinedTable(models.NibrsOffender,
                           prefix='offender',
                           parent=offense)
    tables.append(offender)
    victim = JoinedTable(models.NibrsVictim, prefix='victim', parent=offense)
    tables.append(victim)
    arrestee = JoinedTable(models.NibrsArrestee,
                           prefix='arrestee',
                           parent=offense,
                           join=(models.NibrsIncident.incident_id ==
                                 models.NibrsArrestee.incident_id))
    tables.append(arrestee)
    tables.append(JoinedTable(offender_age,
                              join=(models.NibrsOffender.age_id ==
                                    offender_age.age_id),
                              prefix='offender',
                              parent=offender))
    tables.append(JoinedTable(offender_race,
                              join=(models.NibrsOffender.race_id ==
                                    offender_race.race_id),
                              prefix='offender',
                              parent=offender))
    tables.append(JoinedTable(offender_ethnicity,
                              join=(models.NibrsOffender.ethnicity_id ==
                                    offender_ethnicity.ethnicity_id),
                              prefix='offender',
                              parent=offender))
    tables.append(JoinedTable(victim_age,
                              join=(models.NibrsVictim.age_id ==
                                    victim_age.age_id),
                              prefix='victim',
                              parent=victim))
    tables.append(JoinedTable(victim_race,
                              join=(models.NibrsVictim.race_id ==
                                    victim_race.race_id),
                              prefix='victim',
                              parent=victim))
    tables.append(JoinedTable(victim_ethnicity,
                              join=(models.NibrsVictim.ethnicity_id ==
                                    victim_ethnicity.ethnicity_id),
                              prefix='victim',
                              parent=victim))
    tables.append(JoinedTable(arrestee_age,
                              join=(models.NibrsArrestee.age_id ==
                                    arrestee_age.age_id),
                              prefix='arrestee',
                              parent=arrestee))
    tables.append(JoinedTable(arrestee_race,
                              join=(models.NibrsArrestee.race_id ==
                                    arrestee_race.race_id),
                              prefix='arrestee',
                              parent=arrestee))
    tables.append(JoinedTable(arrestee_ethnicity,
                              join=(models.NibrsArrestee.ethnicity_id ==
                                    arrestee_ethnicity.ethnicity_id),
                              prefix='arrestee',
                              parent=arrestee))
    property = JoinedTable(models.NibrsProperty)
    tables.append(property)
    tables.append(JoinedTable(models.NibrsPropLossType, parent=property))
    # TODO: property_desc, suspected_drug
    tables.append(JoinedTable(models.NibrsLocationType,
                              parent=offense,
                              join=(models.NibrsOffense.location_id ==
                                    models.NibrsLocationType.location_id), ))
    # TODO: COUNTY, TRIBE


class IncidentCountTableFamily(TableFamily):

    base_table = JoinedTable(models.RetaMonthOffenseSubcat)

    tables = []
    month = JoinedTable(models.RetaMonth)
    tables.append(month)
    subcat = JoinedTable(models.RetaOffenseSubcat)
    tables.append(subcat)
    offense = JoinedTable(models.RetaOffense, parent=subcat)
    tables.append(offense)
    tables.append(JoinedTable(models.OffenseClassification, parent=offense))
    tables.append(JoinedTable(models.RetaOffenseCategory, parent=offense))
    tables.extend(TableFamily.agency_tables(month))

    def base_query(self):
        return db.session.query(
            label('actual_count',
                  func.sum(models.RetaMonthOffenseSubcat.actual_count)), label(
                      'reported_count',
                      func.sum(models.RetaMonthOffenseSubcat.reported_count)),
            label('unfounded_count',
                  func.sum(models.RetaMonthOffenseSubcat.unfounded_count)),
            label('cleared_count',
                  func.sum(models.RetaMonthOffenseSubcat.cleared_count)),
            label('juvenile_cleared_count',
                  func.sum(
                      models.RetaMonthOffenseSubcat.juvenile_cleared_count), ))


def _is_string(col):
    col0 = list(col.base_columns)[0]
    return issubclass(col0.type.python_type, str)
