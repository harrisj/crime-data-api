# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import csv
import io
from os import getenv

import flask_restful as restful
from flask import Flask, render_template

import crime_data.resources.agencies
import crime_data.resources.arrests
import crime_data.resources.incidents
import crime_data.resources.offenses
import crime_data.resources.codes
import crime_data.resources.arson
import crime_data.resources.meta
import crime_data.resources.offenders
import crime_data.resources.victims
import crime_data.resources.cargo_theft
import crime_data.resources.hate_crime
import crime_data.resources.geo

from crime_data import commands
from crime_data.assets import assets
from crime_data.common.marshmallow_schemas import ma
from crime_data.common.models import db
from crime_data.common.credentials import get_credential
from crime_data.extensions import (cache, debug_toolbar, migrate)
from flask_apispec.extension import FlaskApiSpec
from crime_data.settings import ProdConfig

if __name__ == '__main__':
    app.run(debug=True)  # nosec, this isn't called on production


def create_app(config_object=ProdConfig):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_newrelic(app)
    add_resources(app)
    register_commands(app)
    db.init_app(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    assets.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    ma.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    return None


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {'db': db}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)


def add_resources(app):
    """Register API routes and Swagger endpoints"""
    api = restful.Api(app)

    @api.representation('text/csv')
    def output_csv(data, code, headers=None):
        """Curl with -H "Accept: text/csv" """
        outfile = io.StringIO()
        keys = data[0].keys()
        writer = csv.DictWriter(outfile, keys)
        writer.writerows(data)
        outfile.seek(0)
        resp = api.make_response(outfile.read(), code)
        resp.headers.extend(headers or {})
        return resp

    api.add_resource(crime_data.resources.agencies.AgenciesList, '/agencies/')
    api.add_resource(crime_data.resources.agencies.AgenciesDetail,
                     '/agencies/<string:nbr>/')

    api.add_resource(crime_data.resources.incidents.IncidentsList,
                     '/incidents/')
    api.add_resource(crime_data.resources.incidents.CachedIncidentsCount,
                     '/incidents/count/')
    api.add_resource(crime_data.resources.incidents.IncidentsDetail,
                     '/incidents/<int:id>/')
    api.add_resource(crime_data.resources.offenses.OffensesList, '/offenses/')
    api.add_resource(crime_data.resources.codes.CodeReferenceIndex,
                     '/codes')
    api.add_resource(crime_data.resources.codes.CodeReferenceList,
                     '/codes/<string:code_table>.<string:output>',
                     '/codes/<string:code_table>')
    api.add_resource(crime_data.resources.arrests.ArrestsCountByRace,
                     '/arrests/race/')
    api.add_resource(crime_data.resources.arrests.ArrestsCountByEthnicity,
                     '/arrests/ethnicity/')
    api.add_resource(crime_data.resources.arrests.ArrestsCountByAgeSex,
                     '/arrests/age_sex/')
    api.add_resource(crime_data.resources.arson.ArsonCountResource,
                     '/arson/')
    api.add_resource(crime_data.resources.meta.MetaDetail,
                     '/meta/<path:endpoint>')
    api.add_resource(crime_data.resources.geo.StateDetail,
                     '/geo/states/<string:id>')
    api.add_resource(crime_data.resources.geo.StateParticipation,
                     '/geo/states/<int:state_id>/participation',
                     '/geo/states/<string:state_abbr>/participation')

    api.add_resource(crime_data.resources.geo.CountyDetail,
                     '/geo/counties/<string:fips>')


    api.add_resource(crime_data.resources.offenses.OffensesCountNational,
                     '/offenses/count/national/<string:variable>')
    api.add_resource(crime_data.resources.offenses.OffensesCountStates,
                     '/offenses/count/states/<int:state_id>/<string:variable>')
    api.add_resource(crime_data.resources.offenses.OffensesCountCounties,
                     '/offenses/count/counties/<string:variable>')


    api.add_resource(crime_data.resources.offenders.OffendersCountNational,
                     '/offenders/count/national/<string:variable>')
    api.add_resource(crime_data.resources.offenders.OffendersCountStates,
                     '/offenders/count/states/<int:state_id>/<string:variable>')
    api.add_resource(crime_data.resources.victims.VictimsCountNational,
                     '/victims/count/national/<string:variable>')
    api.add_resource(crime_data.resources.victims.VictimsCountStates,
                     '/victims/count/states/<int:state_id>/<string:variable>')
    api.add_resource(crime_data.resources.offenders.OffendersCountCounties,
                     '/offenders/count/counties/<int:county_id>/<string:variable>')
    api.add_resource(crime_data.resources.victims.VictimsCountCounties,
                     '/victims/count/counties/<int:county_id>/<string:variable>')

    api.add_resource(crime_data.resources.cargo_theft.CargoTheftsCountNational,
                     '/ct/count/national/<string:variable>')
    api.add_resource(crime_data.resources.cargo_theft.CargoTheftsCountCounties,
                     '/ct/count/counties/<int:county_id>/<string:variable>')
    api.add_resource(crime_data.resources.cargo_theft.CargoTheftsCountStates,
                     '/ct/count/states/<int:state_id>/<string:variable>')

    api.add_resource(crime_data.resources.hate_crime.HateCrimesCountNational,
                     '/hc/count/national/<string:variable>')
    api.add_resource(crime_data.resources.hate_crime.HateCrimesCountCounties,
                     '/hc/count/counties/<int:county_id>/<string:variable>')
    api.add_resource(crime_data.resources.hate_crime.HateCrimesCountStates,
                     '/hc/count/states/<int:state_id>/<string:variable>')
    api.add_resource(crime_data.resources.victims.VictimOffenseSubcounts,
                     '/victims/count/states/<int:state_id>/<string:variable>/offenses',
                     '/victims/count/national/<string:variable>/offenses')
    api.add_resource(crime_data.resources.offenders.OffenderOffenseSubcounts,
                     '/offenders/count/states/<int:state_id>/<string:variable>/offenses',
                     '/offenders/count/national/<string:variable>/offenses')
    api.add_resource(crime_data.resources.hate_crime.HateCrimeOffenseSubcounts,
                     '/hc/count/states/<int:state_id>/<string:variable>/offenses',
                     '/hc/count/national/<string:variable>/offenses')
    api.add_resource(crime_data.resources.cargo_theft.CargoTheftOffenseSubcounts,
                     '/ct/count/states/<int:state_id>/<string:variable>/offenses',
                     '/ct/count/national/<string:variable>/offenses')

    docs = FlaskApiSpec(app)
    docs.register(crime_data.resources.agencies.AgenciesDetail)
    docs.register(crime_data.resources.agencies.AgenciesList)
    docs.register(crime_data.resources.incidents.CachedIncidentsCount)
    docs.register(crime_data.resources.incidents.IncidentsDetail)
    docs.register(crime_data.resources.incidents.IncidentsList)
    docs.register(crime_data.resources.offenses.OffensesList)
    docs.register(crime_data.resources.arrests.ArrestsCountByRace)
    docs.register(crime_data.resources.arrests.ArrestsCountByEthnicity)
    docs.register(crime_data.resources.arrests.ArrestsCountByAgeSex)
    docs.register(crime_data.resources.meta.MetaDetail)
    docs.register(crime_data.resources.geo.StateDetail)
    docs.register(crime_data.resources.geo.CountyDetail)
    docs.register(crime_data.resources.offenders.OffendersCountNational)
    docs.register(crime_data.resources.offenders.OffendersCountStates)
    docs.register(crime_data.resources.offenders.OffendersCountCounties)
    docs.register(crime_data.resources.victims.VictimsCountNational)
    docs.register(crime_data.resources.victims.VictimsCountStates)
    docs.register(crime_data.resources.victims.VictimsCountCounties)
    docs.register(crime_data.resources.cargo_theft.CargoTheftsCountNational)
    docs.register(crime_data.resources.cargo_theft.CargoTheftsCountStates)
    docs.register(crime_data.resources.cargo_theft.CargoTheftsCountCounties)
    docs.register(crime_data.resources.hate_crime.HateCrimesCountNational)
    docs.register(crime_data.resources.hate_crime.HateCrimesCountStates)
    docs.register(crime_data.resources.hate_crime.HateCrimesCountCounties)
    docs.register(crime_data.resources.victims.VictimOffenseSubcounts)
    docs.register(crime_data.resources.offenders.OffenderOffenseSubcounts)
    docs.register(crime_data.resources.cargo_theft.CargoTheftOffenseSubcounts)
    docs.register(crime_data.resources.hate_crime.HateCrimeOffenseSubcounts)

def newrelic_status_endpoint():
    return 'OK'


def register_newrelic(app):
    """Setup New Relic monitoring for the application"""

    app.add_url_rule('/status', 'status', newrelic_status_endpoint)

    try:
        license_key = get_credential('NEW_RELIC_API_KEY')
        import newrelic.agent
        settings = newrelic.agent.global_settings()
        settings.license_key = license_key
        newrelic.agent.initialize()
    except: #nosec
        pass
