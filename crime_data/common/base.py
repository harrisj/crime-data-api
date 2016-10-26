import json
import os
import random

from flask_restful import Resource
# import celery
from flask_sqlalchemy import SignallingSession, SQLAlchemy


class RoutingSession(SignallingSession):
    """Route requests to database leader or follower as appropriate.
    Based on http://techspot.zzzeek.org/2012/01/11/django-style-database-routers-in-sqlalchemy/
    """

    @property
    def followers(self):
        return self.app.config['SQLALCHEMY_FOLLOWERS']

    @property
    def follower_tasks(self):
        return self.app.config['SQLALCHEMY_FOLLOWER_TASKS']

    @property
    def restrict_follower_traffic_to_tasks(self):
        return self.app.config['SQLALCHEMY_RESTRICT_FOLLOWER_TRAFFIC_TO_TASKS']

    @property
    def use_follower(self):
        # Check for read operations and configured followers.
        use_follower = (not self._flushing and self.followers)

        # Optionally restrict traffic to followers for only supported tasks.
        # if use_follower and self.restrict_follower_traffic_to_tasks:
        #     use_follower = (
        #         celery.current_task and
        #         celery.current_task.name in self.follower_tasks
        #     )

        return use_follower

    def get_bind(self, mapper=None, clause=None):
        if self.use_follower:
            return random.choice(self.followers)

        return super().get_bind(mapper=mapper, clause=clause)


class RoutingSQLAlchemy(SQLAlchemy):
    def create_session(self, options):
        return RoutingSession(self, **options)


class CdeResource(Resource):
    __abstract__ = True
    schema = None

    def _stringify(self, data):
        """Avoid JSON serialization errors
        by converting values in list of dicts
        into strings."""
        return [{k: (d[k] if hasattr(d[k], '__pow__') else str(d[k]))
                 for k in d} for d in (r._asdict() for r in data)]

    def _as_dict(self, fieldTuple, res):
        return dict(zip(fieldTuple, res))

    def with_metadata(self, results, args):
        results = results.paginate(args['page'], args['per_page'])
        if self.schema:
            items = self.schema.dump(results.items).data
        else:
            items = self._stringify(results.items)
        return {'results': items,
                'pagination': {
                    'count': results.total,
                    'page': results.page,
                    'pages': results.pages,
                    'per_page': results.per_page,
                }, }

    def verify_api_key(self, args):
        if os.getenv('VCAP_SERVICES'):
            service_env = json.loads(os.getenv('VCAP_SERVICES'))
            cups_name = 'crime-data-api-creds'
            creds = [u['credentials']
                     for u in service_env['user-provided']
                     if 'credentials' in u]
            key = creds[0]['API_KEY']
            if args['api_key'] != key:
                raise Exception('Ask Catherine for API key')


db = RoutingSQLAlchemy()


class BaseModel(db.Model):
    __abstract__ = True
    idx = db.Column(db.Integer, primary_key=True)
