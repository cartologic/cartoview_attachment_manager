from cartoview.app_manager.models import AppInstance
from django.conf import settings
from django.db import connection
from uuid import uuid4
from django.db import models
from django.contrib import admin


# from attachment_manager.models import BasicModel


def create_comment_table(layer_name):
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
      identifier character varying(256) NOT NULL,
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


def create_file_table(layer_name):
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
      identifier character varying(256) NOT NULL,
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


def create_rating_table(layer_name):
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
      identifier character varying(256) NOT NULL,
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


UserModel = settings.AUTH_USER_MODEL
BASE_FIELDS = {
    'created_at': models.DateTimeField(auto_now_add=True),
    'updated_at': models.DateTimeField(auto_now=True),
    'user': models.ForeignKey(UserModel, related_name="attachment_%(class)s"),
    'app_instance': models.ForeignKey(AppInstance, related_name="attachment_%(class)s", blank=True, null=True),
    'feature': models.PositiveIntegerField(blank=True, null=True),
    'identifier': models.CharField(max_length=256),
}


def create_comment_model(name, layer_name, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Function creates a Model for Comments to deal with existing table
    name => ClassName
    layer_name => paramter added to prefix to get the full table name
    Example : create_comment_model('Comment','hisham',app_label='fake_app',module='fake_project.fake_app.no_models')
     """
    create_comment_table(layer_name)
    fields = BASE_FIELDS.copy()
    fields.update({'comment': models.TextField()})
    options = {
        'db_table': 'attachment_manager_comment_{0}'.format(layer_name),
    }
    """
    Create specified model
    """

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


def create_file_model(name, layer_name, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model
    Function creates a Model for Files to deal with existing table
    name => ClassName
    layer_name => paramter added to prefix to get the full table name
    Example : create_file_model('Comment','hisham',app_label='fake_app',module='fake_project.fake_app.no_models')
     """
    create_file_table(layer_name)
    fields = BASE_FIELDS.copy()
    fields.update({
        'file': models.BinaryField(),
        'file_name': models.CharField(max_length=150),
        'is_image': models.BooleanField(default=False)
    })
    options = {
        'db_table': 'attachment_manager_file_{0}'.format(layer_name),
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


def check_table_exists(table_name):
    """this function check if table exists in the database or not Return True or Flase"""
    with connection.cursor() as cursor:
        cursor.execute("""\
       SELECT EXISTS (
       SELECT 1
       FROM   information_schema.tables
       WHERE  table_schema = 'public'
       AND    table_name = '{0}'
       );""".format(table_name))
        exists = cursor.fetchone()[0]
        return exists
