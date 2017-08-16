from django.conf import settings
from datetime import datetime
import json


def get_connection_paramters():
    datastore = settings.OGC_SERVER.get(
        'default', {}).get('DATASTORE', 'datastore')
    database = settings.DATABASES.get(datastore, {})
    if database.get('ENGINE', '') == 'django.contrib.gis.db.backends.postgis':
        connection_params = {
            'user': database.get('USER', None),
            'password': database.get("PASSWORD", None),
            'host': database.get('HOST', None)
        }
        return (database.get('NAME', None), connection_params)
    else:
        raise ValueError(
            'could not find django.contrib.gis.db.backends.postgis ENGINE')


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)
# def check_required_fields
