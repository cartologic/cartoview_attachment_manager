import base64
import json
from datetime import datetime
import os
from django.conf import settings


def get_connection_paramters():
    datastore = settings.OGC_SERVER.get(
        'default', {}).get('DATASTORE', os.getenv('DEFAULT_BACKEND_DATASTORE',
                                                  'datastore'))
    database = settings.DATABASES.get(datastore, None)
    if database:
        connection_params = {
            'user': database.get('USER', None),
            'password': database.get("PASSWORD", None),
            'host': database.get('HOST', 'localhost'),
            'port': database.get('PORT', '5432')
        }
        return (database.get('NAME', None), connection_params)
    else:
        raise ValueError(
            'Attachment manager cannot find datastore backend DATASTORE: %-10s'
            % (database))


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, buffer):
            return base64.b64encode(o)
        return json.JSONEncoder.default(self, o)
