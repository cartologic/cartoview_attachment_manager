import os

import gc
from avatar.templatetags.avatar_tags import avatar_url
from cartoview.app_manager.models import AppInstance
from cartoview.app_manager.rest import AppInstanceResource
from django.conf import settings
from django.db import connection
from uuid import uuid4
from django.db import models
from django.contrib import admin

# from attachment_manager.models import BasicModel
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource


def create_comment_table(layer_name, db='default'):
    COMMENT_TABLE = """\
    CREATE SEQUENCE IF NOT EXISTS public.attachment_manager_comment_{0}_id_seq
      INCREMENT 1
      MINVALUE 1
      MAXVALUE 9223372036854775807
      START 1
      CACHE 1;
    ALTER TABLE public.attachment_manager_comment_{0}_id_seq
      OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS public.attachment_manager_comment_{0}
    (
      id integer NOT NULL DEFAULT nextval('attachment_manager_comment_{0}_id_seq'::regclass),
      created_at timestamp with time zone NOT NULL,
      updated_at timestamp with time zone NOT NULL,
      feature integer,
      identifier character varying(256),
      comment text NOT NULL,
      app_instance_id integer,
      user_id integer NOT NULL,
      CONSTRAINT attachment_manager_comment_{0}_{1}_pkey PRIMARY KEY (id),
      CONSTRAINT "{1}" FOREIGN KEY (app_instance_id)
          REFERENCES public.app_manager_appinstance (resourcebase_ptr_id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT attachment_manage_user_id_{0}_{1}_fk_people_profile_id FOREIGN KEY (user_id)
          REFERENCES public.people_profile (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT attachment_manager_comment_{0}_{1}_feature_check CHECK (feature >= 0)
    )
    WITH (
      OIDS=FALSE
    );
    ALTER TABLE public.attachment_manager_comment_{0}
      OWNER TO postgres;

    CREATE INDEX IF NOT EXISTS attachment_manager_comment_{0}_{2}
      ON public.attachment_manager_comment_{0}
      USING btree
      (app_instance_id);

    CREATE INDEX IF NOT EXISTS attachment_manager_comment_{0}_{3}
      ON public.attachment_manager_comment_{0}
      USING btree
      (user_id);

    """.format(layer_name, str(uuid4()).replace('-', ""), str(uuid4()).replace('-', ""), str(uuid4()).replace('-', ""))
    with connection.cursor() as cursor:
        cursor.execute(COMMENT_TABLE)


def create_file_table(layer_name, db='default'):
    FILE_TABLE = """\
    CREATE SEQUENCE IF NOT EXISTS public.attachment_manager_file_{0}_id_seq
          INCREMENT 1
          MINVALUE 1
          MAXVALUE 9223372036854775807
          START 1
          CACHE 1;
    ALTER TABLE public.attachment_manager_file_{0}_id_seq
      OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS public.attachment_manager_file_{0}
    (
      id integer NOT NULL DEFAULT nextval('attachment_manager_file_{0}_id_seq'::regclass),
      created_at timestamp with time zone NOT NULL,
      updated_at timestamp with time zone NOT NULL,
      feature integer,
      identifier character varying(256),
      file bytea NOT NULL,
      file_name character varying(150) NOT NULL,
      is_image boolean NOT NULL,
      app_instance_id integer,
      user_id integer NOT NULL,
      CONSTRAINT attachment_manager_file_{0}_{1}_pkey PRIMARY KEY (id),
      CONSTRAINT "{1}" FOREIGN KEY (app_instance_id)
          REFERENCES public.app_manager_appinstance (resourcebase_ptr_id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT attachment_manager_user_id_{0}_{1}_fk_people_profile_id FOREIGN KEY (user_id)
          REFERENCES public.people_profile (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT attachment_manager_file_{0}_{1}_feature_check CHECK (feature >= 0)
    )
    WITH (
      OIDS=FALSE
    );
    ALTER TABLE public.attachment_manager_file_{0}
      OWNER TO postgres;


    CREATE INDEX IF NOT EXISTS attachment_manager_file_{0}_{2}
      ON public.attachment_manager_file_{0}
      USING btree
      (app_instance_id);


    CREATE INDEX IF NOT EXISTS attachment_manager_file_{0}_{3}
      ON public.attachment_manager_file_{0}
      USING btree
      (user_id);

    """.format(layer_name, str(uuid4()).replace('-', ""), str(uuid4()).replace('-', ""), str(uuid4()).replace('-', ""))
    with connection.cursor() as cursor:
        cursor.execute(FILE_TABLE)


def create_rating_table(layer_name, db='default'):
    RATING_TABLE = """\
    CREATE SEQUENCE IF NOT EXISTS public.attachment_manager_rating_{0}_id_seq
          INCREMENT 1
          MINVALUE 1
          MAXVALUE 9223372036854775807
          START 1
          CACHE 1;
    ALTER TABLE public.attachment_manager_file_{0}_id_seq
      OWNER TO postgres;
    CREATE TABLE IF NOT EXISTS public.attachment_manager_rating_{0}
    (
      id integer NOT NULL DEFAULT nextval('attachment_manager_rating_{0}_id_seq'::regclass),
      created_at timestamp with time zone NOT NULL,
      updated_at timestamp with time zone NOT NULL,
      feature integer,
      identifier character varying(256),
      rate smallint NOT NULL,
      app_instance_id integer,
      user_id integer NOT NULL,
      CONSTRAINT attachment_manager_rating_{0}_{1}_pkey PRIMARY KEY (id),
      CONSTRAINT attachment_manage_user_id_{0}_{1}_fk_people_profile_id FOREIGN KEY (user_id)
          REFERENCES public.people_profile (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT {1} FOREIGN KEY (app_instance_id)
          REFERENCES public.app_manager_appinstance (resourcebase_ptr_id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT attachment_manager_rating_{0}_{1}_feature_check CHECK (feature >= 0),
      CONSTRAINT attachment_manager_rating_{0}_{1}_rate_check CHECK (rate >= 0)
    )
    WITH (
      OIDS=FALSE
    );
    ALTER TABLE public.attachment_manager_rating_{0}
      OWNER TO postgres;

    CREATE INDEX IF NOT EXISTS attachment_manager_rating_{0}_{2}
      ON public.attachment_manager_rating_{0}
      USING btree
      (app_instance_id);

    CREATE INDEX IF NOT EXISTS attachment_manager_rating_{0}_{3}
      ON public.attachment_manager_rating_{0}
      USING btree
      (user_id);
    """.format(layer_name, str(uuid4()).replace('-', ""), str(uuid4()).replace('-', ""), str(uuid4()).replace('-', ""))
    with connection.cursor() as cursor:
        cursor.execute(RATING_TABLE)


# TODO Add database option to Models take alook https://docs.djangoproject.com/en/1.10/topics/db/multi-db/
UserModel = settings.AUTH_USER_MODEL
BASE_FIELDS = {
    'created_at': models.DateTimeField(auto_now_add=True),
    'updated_at': models.DateTimeField(auto_now=True),
    'user': models.ForeignKey(UserModel, related_name="attachment_%(class)s"),
    'app_instance': models.ForeignKey(AppInstance, related_name="attachment_%(class)s", blank=True, null=True),
    'feature': models.PositiveIntegerField(blank=True, null=True),
    'identifier': models.CharField(max_length=256, null=True, blank=True),
}

_comments_models_cache = {}

class BaseCommentModel(models.Model):
    # _db = 'default'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(UserModel, related_name="attachment_%(class)s")
    app_instance = models.ForeignKey(AppInstance, related_name="attachment_%(class)s", blank=True, null=True)
    feature = models.PositiveIntegerField(blank=True, null=True)
    identifier = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        abstract = True

def create_comment_model(layer_name):
    if layer_name in _comments_models_cache:
        # print 'from cache: ', layer_name
        return _comments_models_cache[layer_name]
    # print 'creating model: ', layer_name

    table_name = 'attachment_manager_comment_{0}'.format(layer_name)
    if not check_table_exists(table_name):
        create_comment_table(layer_name)

    class Meta:
        db_table = table_name
        managed = False

    model_attrs = {
        '__module__': __name__,  # set module name to current module name
        'Meta': Meta,
    }
    model_attrs.update({'comment': models.TextField()})

    model = type(table_name, (BaseCommentModel,), model_attrs)
    _comments_models_cache[layer_name] = model
    return model



def create_file_model(name, layer_name, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model
    Function creates a Model for Files to deal with existing table
    name => ClassName
    layer_name => paramter added to prefix to get the full table name
    Example : create_file_model('File','hisham',app_label='fake_app',module='fake_project.fake_app.no_models')
     """
    table_name = 'attachment_manager_file_{0}'.format(layer_name)
    if not check_table_exists(table_name):
        create_file_table(layer_name)
    fields = BASE_FIELDS.copy()
    fields.update({
        'file': models.BinaryField(),
        'file_name': models.CharField(max_length=150),
        'is_image': models.BooleanField(default=False)
    })
    options = {
        'db_table': table_name,
    }

    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)

    # Create the class, which automatically triggers ModelBase processing
    model = type(name, (models.Model,), attrs)

    # Create an Admin class if admin options were provided
    if admin_opts is not None:
        class Admin(admin.ModelAdmin):
            pass

        for key, value in admin_opts:
            setattr(Admin, key, value)
        admin.site.register(model, Admin)

    return model


def create_rating_model(name, layer_name, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model
    Function creates a Model for Rating to deal with existing table
    name => ClassName
    layer_name => paramter added to prefix to get the full table name
    Example : create_file_model('Rating','hisham',app_label='fake_app',module='fake_project.fake_app.no_models')
     """
    table_name = 'attachment_manager_rating_{0}'.format(layer_name)
    if not check_table_exists(table_name):
        create_rating_table(layer_name)
    fields = BASE_FIELDS.copy()
    fields.update({'rate': models.PositiveSmallIntegerField(), })
    options = {
        'db_table': table_name,
    }

    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)

    # Create the class, which automatically triggers ModelBase processing
    model = type(name, (models.Model,), attrs)

    # Create an Admin class if admin options were provided
    if admin_opts is not None:
        class Admin(admin.ModelAdmin):
            pass

        for key, value in admin_opts:
            setattr(Admin, key, value)
        admin.site.register(model, Admin)

    return model


def test():
    from geonode.people.models import Profile
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_data')
    file_path = os.path.join(data_path, 'image.png')
    with open(file_path) as f:
        file = f.read()
    model = create_file_model('File', 'hisham', app_label='fake_app', module='fake_project.fake_app.no_models')
    model.objects.create(file=file, file_name=os.path.basename(file_path), is_image=True, user=Profile.objects.all()[0])


def test_read():
    # from PIL import Image
    # import io
    # model = create_file_model('File', 'hisham', app_label='fake_app', module='fake_project.fake_app.no_models')
    # image_data = model.objects.all()[0].file
    # image = Image.open(io.BytesIO(image_data))
    # image.show()
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_data')
    model = create_file_model('File', 'hisham', app_label='fake_app', module='fake_project.fake_app.no_models')
    obj = model.objects.all().last()
    with open(os.path.join(data_path, 'output_' + obj.file_name), 'wb') as f:
        f.write(obj.file)


class CommentBaseResource(ModelResource):
    def save(self, bundle, skip_errors=False):
        bundle.obj.user = bundle.request.user
        return super(CommentBaseResource, self).save(bundle, skip_errors)

    def dehydrate_user(self, bundle):
        return dict(username=bundle.obj.user.username, avatar=avatar_url(bundle.obj.user, 60))


def create_comment_resource(name, model, fields=None, module=''):
    fields = {'user': fields.DictField(readonly=True)}
    fields.update({'rate': models.PositiveSmallIntegerField(), })
    options = {
        'queryset': model.objects.all(),
        'filtering': {"identifier": ALL,
                      'feature': ALL,
                      'app_instance': ALL_WITH_RELATIONS},
        'can_edit': True,
        'authorization': Authorization()
    }

    class Meta:
        pass

    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)
    attrs = {'__module__': module, 'Meta': Meta}
    if fields:
        attrs.update(fields)
    resource = type(name, (CommentBaseResource,), attrs)

    return resource


def check_table_exists(table_name, schema='public'):
    """this function check if table exists in the database or not Return True or Flase"""
    with connection.cursor() as cursor:
        cursor.execute("""\
       SELECT EXISTS (
   SELECT 1
   FROM   pg_tables
   WHERE  schemaname = '{1}'
   AND    tablename = '{0}'
   );""".format(table_name, schema))
        exists = cursor.fetchone()[0]
        return exists
