import django
from avatar.templatetags.avatar_tags import avatar_url
from cartoview.app_manager.rest import AppInstanceResource
from django.core.exceptions import MultipleObjectsReturned, ImproperlyConfigured
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import QUERY_TERMS
from tastypie.constants import ALL_WITH_RELATIONS, ALL
from tastypie.authorization import Authorization
from tastypie.exceptions import BadRequest, InvalidFilterError, NotFound
from tastypie.resources import ModelResource
from tastypie import fields
from .dynamic import *
from cartoview.app_manager.api import rest_api
from tastypie.utils import (
    dict_strip_unicode_keys, is_valid_jsonp_callback_value, string_to_python,
    trailing_slash,
)

try:
    from django.contrib.gis.db.models.fields import GeometryField
except (ImproperlyConfigured, ImportError):
    GeometryField = None


class BaseAttachment(ModelResource):
    user = fields.DictField(readonly=True)
    app_instance = fields.ForeignKey(AppInstanceResource, 'app_instance', null=True, blank=True)
    created_at = fields.ApiField('created_at', readonly=True)
    updated_at = fields.ApiField('updated_at', readonly=True)
    feature = fields.ApiField('feature', null=True, blank=True)

    class Meta:
        filtering = {"app_instance": ALL_WITH_RELATIONS,
                     "feature": ALL}
        can_edit = True
        authorization = Authorization()


class CommentResource(BaseAttachment):
    comment = fields.ApiField('comment')

    def get_object_list(self, request):
        layer_name = request.GET.get('layer_name', None)
        if layer_name:
            model = create_comment_model(layer_name)
            return model.objects.all()
        else:
            raise BadRequest("layer_name paramter not found")

    def save(self, bundle, skip_errors=False):
        bundle.obj.user = bundle.request.user
        layer_name = bundle.request.GET.get('layer_name', None)
        if layer_name:
            return super(CommentResource, self).save(bundle, skip_errors)

    def obj_create(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_create``.
        """
        layer_name = bundle.request.GET.get('layer_name', None)
        if layer_name:
            model = create_comment_model(layer_name)
            bundle.obj = model()

            for key, value in kwargs.items():
                setattr(bundle.obj, key, value)

            bundle = self.full_hydrate(bundle)
            return self.save(bundle)

        else:
            raise BadRequest("layer_name paramter not Provided")

    def build_filters_custom(self, queryset, filters=None, ignore_bad_filters=False):
        """
        Given a dictionary of filters, create the necessary ORM-level filters.

        Keys should be resource fields, **NOT** model fields.

        Valid values are either a list of Django filter types (i.e.
        ``['startswith', 'exact', 'lte']``), the ``ALL`` constant or the
        ``ALL_WITH_RELATIONS`` constant.
        """
        # At the declarative level:
        #     filtering = {
        #         'resource_field_name': ['exact', 'startswith', 'endswith', 'contains'],
        #         'resource_field_name_2': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        #         'resource_field_name_3': ALL,
        #         'resource_field_name_4': ALL_WITH_RELATIONS,
        #         ...
        #     }
        # Accepts the filters as a dict. None by default, meaning no filters.
        if filters is None:
            filters = {}

        qs_filters = {}

        if queryset:
            # Get the possible query terms from the current QuerySet.
            query_terms = queryset.query.query_terms
        else:
            query_terms = QUERY_TERMS
        if django.VERSION >= (1, 8) and GeometryField:
            query_terms = query_terms | set(GeometryField.class_lookups.keys())

        for filter_expr, value in filters.items():
            filter_bits = filter_expr.split(LOOKUP_SEP)
            field_name = filter_bits.pop(0)
            filter_type = 'exact'

            if field_name not in self.fields:
                # It's not a field we know about. Move along citizen.
                continue

            if len(filter_bits) and filter_bits[-1] in query_terms:
                filter_type = filter_bits.pop()

            try:
                lookup_bits = self.check_filtering(field_name, filter_type, filter_bits)
            except InvalidFilterError:
                if ignore_bad_filters:
                    continue
                else:
                    raise
            value = self.filter_value_to_python(value, field_name, filters, filter_expr, filter_type)

            db_field_name = LOOKUP_SEP.join(lookup_bits)
            qs_filter = "%s%s%s" % (db_field_name, LOOKUP_SEP, filter_type)
            qs_filters[qs_filter] = value

        return dict_strip_unicode_keys(qs_filters)

    def obj_get_list(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_get_list``.

        ``GET`` dictionary of bundle.request can be used to narrow the query.
        """
        layer_name = bundle.request.GET.get('layer_name', None)
        if layer_name:
            model = create_comment_model(layer_name)
            filters = {}

            if hasattr(bundle.request, 'GET'):
                # Grab a mutable copy.
                filters = bundle.request.GET.copy()

            # Update with the provided kwargs.
            filters.update(kwargs)
            applicable_filters = self.build_filters_custom(queryset=model.objects.all(), filters=filters)

            try:
                objects = self.apply_filters(bundle.request, applicable_filters)
                return self.authorized_read_list(objects, bundle)
            except ValueError:
                raise BadRequest("Invalid resource lookup data provided (mismatched type).")
        else:
            raise BadRequest("layer_name paramter not found")

    def obj_get(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_get``.

        Takes optional ``kwargs``, which are used to narrow the query to find
        the instance.
        """
        # Use ignore_bad_filters=True. `obj_get_list` filters based on
        # request.GET, but `obj_get` usually filters based on `detail_uri_name`
        # or data from a related field, so we don't want to raise errors if
        # something doesn't explicitly match a configured filter.
        layer_name = bundle.request.GET.get('layer_name', None)
        if layer_name:
            model = create_comment_model(layer_name)
            applicable_filters = self.build_filters_custom(queryset=model.objects.all(), filters=kwargs,
                                                           ignore_bad_filters=True)
            if self._meta.detail_uri_name in kwargs:
                applicable_filters[self._meta.detail_uri_name] = kwargs[self._meta.detail_uri_name]

            try:
                object_list = self.apply_filters(bundle.request, applicable_filters)
                stringified_kwargs = ', '.join(["%s=%s" % (k, v) for k, v in applicable_filters.items()])

                if len(object_list) <= 0:
                    raise self._meta.object_class.DoesNotExist(
                        "Couldn't find an instance of '%s' which matched '%s'." % (
                            self._meta.object_class.__name__, stringified_kwargs))
                elif len(object_list) > 1:
                    raise MultipleObjectsReturned(
                        "More than '%s' matched '%s'." % (model.__name__, stringified_kwargs))

                bundle.obj = object_list[0]
                self.authorized_read_detail(object_list, bundle)
                return bundle.obj
            except ValueError:
                raise NotFound("Invalid resource lookup data provided (mismatched type).")
        else:
            raise BadRequest("layer_name paramter not found")

    def dehydrate_user(self, bundle):
        return dict(username=bundle.obj.user.username, avatar=avatar_url(bundle.obj.user, 60))


class FileResource(BaseAttachment):
    file = fields.ApiField('file', null=False)
    file_name = fields.ApiField('file_name', null=False)
    is_image = fields.ApiField('is_image', default=False)

    def get_object_list(self, request):
        layer_name = request.GET.get('layer_name', None)
        if layer_name:
            model = create_file_model(layer_name)
            return model.objects.all()
        else:
            raise BadRequest("layer_name paramter not found")

    def save(self, bundle, skip_errors=False):
        from geonode.people.models import Profile
        u = Profile.objects.last()
        bundle.obj.user = u
        import base64
        bundle.obj.file=base64.b64decode(bundle.obj.file)
        # bundle.obj.user = bundle.request.user
        layer_name = bundle.request.GET.get('layer_name', None)
        if layer_name:
            return super(FileResource, self).save(bundle, skip_errors)

    def obj_create(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_create``.
        """
        layer_name = bundle.request.GET.get('layer_name', None)
        if layer_name:
            model = create_file_model(layer_name)
            bundle.obj = model()

            for key, value in kwargs.items():
                setattr(bundle.obj, key, value)

            bundle = self.full_hydrate(bundle)
            return self.save(bundle)

        else:
            raise BadRequest("layer_name paramter not Provided")

    def build_filters_custom(self, queryset, filters=None, ignore_bad_filters=False):
        """
        Given a dictionary of filters, create the necessary ORM-level filters.

        Keys should be resource fields, **NOT** model fields.

        Valid values are either a list of Django filter types (i.e.
        ``['startswith', 'exact', 'lte']``), the ``ALL`` constant or the
        ``ALL_WITH_RELATIONS`` constant.
        """
        # At the declarative level:
        #     filtering = {
        #         'resource_field_name': ['exact', 'startswith', 'endswith', 'contains'],
        #         'resource_field_name_2': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        #         'resource_field_name_3': ALL,
        #         'resource_field_name_4': ALL_WITH_RELATIONS,
        #         ...
        #     }
        # Accepts the filters as a dict. None by default, meaning no filters.
        if filters is None:
            filters = {}

        qs_filters = {}

        if queryset:
            # Get the possible query terms from the current QuerySet.
            query_terms = queryset.query.query_terms
        else:
            query_terms = QUERY_TERMS
        if django.VERSION >= (1, 8) and GeometryField:
            query_terms = query_terms | set(GeometryField.class_lookups.keys())

        for filter_expr, value in filters.items():
            filter_bits = filter_expr.split(LOOKUP_SEP)
            field_name = filter_bits.pop(0)
            filter_type = 'exact'

            if field_name not in self.fields:
                # It's not a field we know about. Move along citizen.
                continue

            if len(filter_bits) and filter_bits[-1] in query_terms:
                filter_type = filter_bits.pop()

            try:
                lookup_bits = self.check_filtering(field_name, filter_type, filter_bits)
            except InvalidFilterError:
                if ignore_bad_filters:
                    continue
                else:
                    raise
            value = self.filter_value_to_python(value, field_name, filters, filter_expr, filter_type)

            db_field_name = LOOKUP_SEP.join(lookup_bits)
            qs_filter = "%s%s%s" % (db_field_name, LOOKUP_SEP, filter_type)
            qs_filters[qs_filter] = value

        return dict_strip_unicode_keys(qs_filters)

    def obj_get_list(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_get_list``.

        ``GET`` dictionary of bundle.request can be used to narrow the query.
        """
        layer_name = bundle.request.GET.get('layer_name', None)
        if layer_name:
            model = create_file_model(layer_name)
            filters = {}

            if hasattr(bundle.request, 'GET'):
                # Grab a mutable copy.
                filters = bundle.request.GET.copy()

            # Update with the provided kwargs.
            filters.update(kwargs)
            applicable_filters = self.build_filters_custom(queryset=model.objects.all(), filters=filters)

            try:
                objects = self.apply_filters(bundle.request, applicable_filters)
                return self.authorized_read_list(objects, bundle)
            except ValueError:
                raise BadRequest("Invalid resource lookup data provided (mismatched type).")
        else:
            raise BadRequest("layer_name paramter not found")

    def obj_get(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_get``.

        Takes optional ``kwargs``, which are used to narrow the query to find
        the instance.
        """
        # Use ignore_bad_filters=True. `obj_get_list` filters based on
        # request.GET, but `obj_get` usually filters based on `detail_uri_name`
        # or data from a related field, so we don't want to raise errors if
        # something doesn't explicitly match a configured filter.
        layer_name = bundle.request.GET.get('layer_name', None)
        if layer_name:
            model = create_file_model(layer_name)
            applicable_filters = self.build_filters_custom(queryset=model.objects.all(), filters=kwargs,
                                                           ignore_bad_filters=True)
            if self._meta.detail_uri_name in kwargs:
                applicable_filters[self._meta.detail_uri_name] = kwargs[self._meta.detail_uri_name]

            try:
                object_list = self.apply_filters(bundle.request, applicable_filters)
                stringified_kwargs = ', '.join(["%s=%s" % (k, v) for k, v in applicable_filters.items()])

                if len(object_list) <= 0:
                    raise self._meta.object_class.DoesNotExist(
                        "Couldn't find an instance of '%s' which matched '%s'." % (
                            self._meta.object_class.__name__, stringified_kwargs))
                elif len(object_list) > 1:
                    raise MultipleObjectsReturned(
                        "More than '%s' matched '%s'." % (model.__name__, stringified_kwargs))

                bundle.obj = object_list[0]
                self.authorized_read_detail(object_list, bundle)
                return bundle.obj
            except ValueError:
                raise NotFound("Invalid resource lookup data provided (mismatched type).")
        else:
            raise BadRequest("layer_name paramter not found")

    def dehydrate_user(self, bundle):
        return dict(username=bundle.obj.user.username, avatar=avatar_url(bundle.obj.user, 60))

    def dehydrate_file(self, bundle):
        import base64
        return base64.b64encode(bundle.obj.file)
