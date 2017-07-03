import mimetypes
import django
import six
from avatar.templatetags.avatar_tags import avatar_url
from cartoview.app_manager.rest import AppInstanceResource, ProfileResource, ObjectDoesNotExist, url, HttpResponse
from django.core.exceptions import MultipleObjectsReturned, ImproperlyConfigured
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import QUERY_TERMS
from django.utils.encoding import force_text
from tastypie.bundle import Bundle
from tastypie.constants import ALL_WITH_RELATIONS, ALL
from tastypie.authorization import Authorization
from tastypie.exceptions import BadRequest, InvalidFilterError, NotFound, UnsupportedFormat
from tastypie.http import HttpNotFound
from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.serializers import Serializer
from .dynamic import *
try:
    from django.db.models.fields.related import SingleRelatedObjectDescriptor as ReverseOneToOneDescriptor
except ImportError:
    from django.db.models.fields.related_descriptors import ReverseOneToOneDescriptor
from tastypie.utils import (
    dict_strip_unicode_keys, is_valid_jsonp_callback_value, string_to_python,
    trailing_slash,
)
import base64
import os

try:
    from django.contrib.gis.db.models.fields import GeometryField
except (ImproperlyConfigured, ImportError):
    GeometryField = None


class BaseAttachment(ModelResource):
    app_instance = fields.ForeignKey(AppInstanceResource, 'app_instance', null=False, blank=False)
    created_at = fields.ApiField('created_at', readonly=True)
    updated_at = fields.ApiField('updated_at', readonly=True)
    feature = fields.ApiField('feature', default=0)
    user = fields.DictField(readonly=True)
    user_id = fields.IntegerField(attribute='user__pk', readonly=True)

    class Meta:
        filtering = {"app_instance": ALL_WITH_RELATIONS,
                     "feature": ALL,
                     "user_id": ALL}
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
        from geonode.people.models import Profile
        # bundle.obj.user = bundle.request.user
        bundle.obj.user = Profile.objects.all()[1]
        layer_name = bundle.request.GET.get('layer_name', None)
        if layer_name:
            print bundle.obj.app_instance
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

    def full_hydrate(self, bundle):
        """
        Given a populated bundle, distill it and turn it back into
        a full-fledged object instance.
        """
        layer_name = bundle.request.GET.get('layer_name', None)
        if layer_name:
            model = create_comment_model(layer_name)
            bundle.obj = model()
        else:
            raise BadRequest("layer_name paramter not Provided")

        bundle = self.hydrate(bundle)

        for field_name, field_object in self.fields.items():
            if field_object.readonly is True:
                continue

            # Check for an optional method to do further hydration.
            method = getattr(self, "hydrate_%s" % field_name, None)

            if method:
                bundle = method(bundle)

            if field_object.attribute:
                value = field_object.hydrate(bundle)

                # NOTE: We only get back a bundle when it is related field.
                if isinstance(value, Bundle) and value.errors.get(field_name):
                    bundle.errors[field_name] = value.errors[field_name]

                if value is not None or field_object.null:
                    # We need to avoid populating M2M data here as that will
                    # cause things to blow up.
                    if not field_object.is_related:
                        setattr(bundle.obj, field_object.attribute, value)
                    elif not field_object.is_m2m:
                        if value is not None:
                            # NOTE: A bug fix in Django (ticket #18153) fixes incorrect behavior
                            # which Tastypie was relying on.  To fix this, we store value.obj to
                            # be saved later in save_related.
                            try:
                                setattr(bundle.obj, field_object.attribute, value.obj)
                            except (ValueError, ObjectDoesNotExist):
                                bundle.related_objects_to_save[field_object.attribute] = value.obj
                        elif field_object.null:
                            if not isinstance(getattr(bundle.obj.__class__, field_object.attribute, None),
                                              ReverseOneToOneDescriptor):
                                # only update if not a reverse one to one field
                                setattr(bundle.obj, field_object.attribute, value)
                        elif field_object.blank:
                            continue

        return bundle

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
    id = fields.ApiField('pk', readonly=True)
    file = fields.ApiField('file', null=False)
    file_name = fields.ApiField('file_name', null=False, blank=True)
    is_image = fields.ApiField('is_image', default=False)

    class Meta(BaseAttachment.Meta):
        filtering = {"app_instance": ALL_WITH_RELATIONS,
                     "feature": ALL,
                     "is_image": ALL,
                     "file_name": ALL}
        can_edit = True
        authorization = Authorization()

    def deserialize(self, request, data, format=None):
        if not format:
            format = request.Meta.get('CONTENT_TYPE', 'application/json')
        if format == 'application/x-www-form-urlencoded':
            return request.POST
        if format.startswith('multipart'):
            print request.FILES
            data = request.POST.copy()
            data.update(request.FILES)
            # print "################## REQUEST DATA ###########", data
            return data
        return super(FileResource, self).deserialize(request, data, format)

    def get_object_list(self, request):
        layer_name = request.GET.get('layer_name', None)
        if layer_name:
            model = create_file_model(layer_name)
            return model.objects.all()
        else:
            raise BadRequest("layer_name paramter not found")

    def save(self, bundle, skip_errors=False):
        data = bundle.obj.file.read()
        # print "HHHHHHHHHHH FILE HHHHHHHHHHHHHHH", data
        bundle.obj.file = base64.b64encode(data)
        # print "*******", bundle.obj.app_instance
        # from geonode.people.models import Profile
        # bundle.obj.user = Profile.objects.all()[1]
        bundle.obj.user = bundle.request.user
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
        from django.conf import settings
        url = self.get_resource_uri_custom(bundle) + "?layer_name={0}".format(bundle.request.GET.get('layer_name'))
        return url

    def get_resource_uri_custom(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        """
        Handles generating a resource URI.

        If the ``bundle_or_obj`` argument is not provided, it builds the URI
        for the list endpoint.

        If the ``bundle_or_obj`` argument is provided, it builds the URI for
        the detail endpoint.

        Return the generated URI. If that URI can not be reversed (not found
        in the URLconf), it will return an empty string.
        """
        if bundle_or_obj is not None:
            url_name = 'api_fileitem_download'

        try:
            return self._build_reverse_url(url_name, kwargs=self.resource_uri_kwargs(bundle_or_obj))
        except NoReverseMatch:
            return ''

    def dehydrate_resource_uri(self, bundle):
        """
        For the automatically included ``resource_uri`` field, dehydrate
        the URI for the given bundle.

        Returns empty string if no URI can be generated.
        """
        try:
            return self.get_resource_uri(bundle) + "?layer_name={0}".format(bundle.request.GET.get('layer_name'))
        except NotImplementedError:
            return ''
        except NoReverseMatch:
            return ''

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/download/(?P<pk>[\d]+)%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('download'), name="api_fileitem_download"),
        ]

    def download(self, request, **kwargs):
        layer_name = request.GET.get('layer_name', None)
        if layer_name:
            # method check to avoid bad requests
            self.method_check(request, allowed=['get'])
            # Must be done otherwise endpoint will be wide open
            self.is_authenticated(request)
            response = None
            file_pk = kwargs.get('pk', None)
            if file_pk:
                model = create_file_model(layer_name)
                try:
                    obj = model.objects.get(pk=file_pk)
                    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp')
                    path = os.path.join(data_path, obj.file_name)
                    if os.path.exists(path):
                        os.remove(path)
                    with open(path, 'wb') as f:
                        print obj.file
                        f.write(obj.file)
                    type = mimetypes.MimeTypes().guess_type(obj.file_name)[0]
                    with open(path, 'rb') as fh:
                        response = HttpResponse(fh.read(), content_type=type)
                        response['Content-Length'] = os.path.getsize(path)
                        response['Content-Disposition'] = 'attachment; filename={0}'.format(obj.file_name)
                        return response

                except model.DoesNotExist:
                    response = self.create_response(request=request, data={}, response_class=HttpNotFound)

            if not response:
                response = self.create_response(request=request, data={}, response_class=HttpNotFound)

            return response
        else:
            raise BadRequest("layer_name paramter not found")
# response = requests.post('http://localhost/api/file/?layer_name=hisham',headers=headers,files={'file':open('/home/hisham/Desktop/boundless/exchange/docker-compose-unified-search.yml', 'rb')},data={'file_name': 'docker-compose-unified-search.yml', 'is_image': False, 'app_instance':'/api/appinstances/4/'})
