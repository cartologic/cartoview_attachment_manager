import base64
import datetime
import json

from django.core.urlresolvers import reverse
from peewee import (BlobField, BooleanField, CharField, DateTimeField,
                    DoesNotExist, IntegerField, Model, PostgresqlDatabase)
from playhouse.gfk import GFKField, ReverseGFK
from playhouse.shortcuts import model_to_dict
from .utils import DateTimeEncoder, get_connection_paramters

connection_params = get_connection_paramters()
db = PostgresqlDatabase(
    connection_params[0], autocommit=True, autorollback=True,
    **connection_params[1])
db.connect()
_attachment_comment_models_cache = {}
_attachment_file_models_cache = {}


class BaseDateTime(Model):
    created = DateTimeField(default=datetime.datetime.now,
                            formats='%Y-%m-%d %H:%M:%S')
    modified = DateTimeField(formats='%Y-%m-%d %H:%M:%S')

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        return super(BaseDateTime, self).save(*args, **kwargs)

    class Meta:
        database = db


class BaseModel(BaseDateTime):
    '''This is the parent model for all models contains
    basic fields for attachment models'''
    username = CharField(index=True)
    feature_id = CharField(index=True)


class Tag(BaseDateTime):
    tag = CharField()
    object_type = CharField(null=True)
    object_id = IntegerField(null=True)
    object = GFKField('object_type', 'object_id')

    class Meta:
        indexes = (
            (('tag', 'object_type', 'object_id'), True),
        )


Tag._meta.db_table = "cartoview_tags"
if not Tag.table_exists():
    Tag.create_table()


class AttachmentSerializer(object):
    def get_file_url(self, layername, id):
        url = reverse('attachment_download',
                      kwargs={'layername': layername,
                              'id': id})
        return url

    def attachment_to_json(self, queryset, attachment_type, layername, many=True):
        try:
            if many:
                result = []
                for dic, obj in zip(queryset.dicts(), queryset):
                    if attachment_type == "file":
                        url = self.get_file_url(layername, obj.id)
                        dic.update({'file': url})
                    dic.update(
                        {'tags': [t.tag for t in obj.tags]})
                    result.append(dic)
            else:
                result = model_to_dict(queryset, backrefs=True)
                if attachment_type == "file":
                    url = self.get_file_url(layername, queryset.id)
                    result.update({'file': url})
                result.update({'tags': [t.tag for t in queryset.tags]})
            return json.dumps(result,
                              cls=DateTimeEncoder)
        except DoesNotExist:
            return json.dumps({})

    def decode_file_data(self, data):
        file_data = data.get('file', None)
        if file_data:
            file_format, file_data = file_data.split(
                ';base64,') if ';base64,' in file_data else (None, file_data)
        data.update({'file': base64.b64decode(file_data)})
        return data


class AttachmentManager(object):
    '''this class handle models generation'''

    def __init__(self, table_name):
        self.table_name = self.model_name = table_name

    def get_by_id(self, model, id):
        try:
            return model.get(model.id == id)
        except:
            return None

    def generate_comment_model(self):
        model_fields = {
            'text': CharField(index=True),
            'tags': ReverseGFK(Tag, 'object_type', 'object_id')
        }
        model = type(self.model_name, (BaseModel,), model_fields)
        model._meta.db_table = "attachment_%s_comment" % self.table_name
        if not model.table_exists():
            model.create_table()
        _attachment_comment_models_cache[self.table_name] = model
        return model

    def create_comment_model(self):
        model = _attachment_comment_models_cache.get(self.model_name, None)
        return model if model else self.generate_comment_model()

    def generate_file_model(self):
        model_fields = {
            'file': BlobField(),
            'is_image': BooleanField(default=False),
            'file_name': CharField(null=False),
            'tags': ReverseGFK(Tag, 'object_type', 'object_id')
        }
        model = type(self.model_name, (BaseModel,), model_fields)
        model._meta.db_table = "attachment_%s_file" % self.table_name
        if not model.table_exists():
            model.create_table()
        _attachment_file_models_cache[self.table_name] = model
        return model

    def create_file_model(self):
        model = _attachment_file_models_cache.get(self.model_name, None)
        return model if model else self.generate_file_model()
