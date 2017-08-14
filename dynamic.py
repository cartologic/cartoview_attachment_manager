import datetime
from peewee import PostgresqlDatabase, Model, CharField, DateTimeField,\
    IntegerField, fn
from playhouse.shortcuts import model_to_dict
import json
# Replace static paramter with django database Paramters
db = PostgresqlDatabase('cartoview_datastore',
                        user='postgres', password="clogic", host="localhost",
                        autocommit=True, autorollback=True)
db.connect()
_attachment_comment_models_cache = {}


class BaseDateTime(Model):
    created = DateTimeField(default=datetime.datetime.now)
    modified = DateTimeField()

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        return super(BaseDateTime, self).save(*args, **kwargs)

    @classmethod
    def get_json(self, queryset):
        return json.dumps(model_to_dict(queryset.get()))

    class Meta:
        database = db


class BaseModel(BaseDateTime):
    '''This is the parent model for all models contains
    basic fields for attachment models'''
    username = CharField(index=True)
    feature_id = CharField(index=True)

    def set_tags(self, *tags):
        self.tags = 0
        for tag in tags:
            self.tags |= tag.identifier

    def get_tags(self):
        tag_val = self.tags
        i = 1
        identifiers = []
        while tag_val != 0:
            if tag_val & 1:
                identifiers.append(i)
            i <<= 1  # Increase `i` to the next power of 2.
            tag_val >>= 1  # Pop the right-most bit off of tagval.
        return Tag.select().where(Tag.identifier.in_(identifiers))


class Tag(BaseDateTime):
    tag = CharField(unique=True)
    identifier = IntegerField()

    @classmethod
    def add_tag(cls, tag):
        new_tag = Tag.create(
            tag=tag,
            identifier=fn.COALESCE(
                Tag.select(fn.MAX(Tag.identifier) * 2), 1))
        # Re-fetch the newly-created tag so the identifier
        # is populated with the value.
        return Tag.get(Tag.id == new_tag.id)


if not Tag.table_exists():
    Tag.create_table()


class AttachmentManager(object):
    '''this class handle models generation'''

    def __init__(self, table_name):
        self.table_name = self.model_name = table_name

    def generate_filter_with_tag(self, tags):
        tsum = (Tag
                .select(fn.SUM(Tag.identifier))
                .where(Tag.tag << tags)
                .alias('tsum'))  # Alias we will refer to in Attachment query.
        return tsum

    def generate_comment_model(self):
        model_fields = {
            'comment': CharField(index=True),
            'tags': IntegerField(index=True),

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
