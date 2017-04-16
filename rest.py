from avatar.templatetags.avatar_tags import avatar_url
from cartoview.app_manager.rest import AppInstanceResource
from tastypie.constants import ALL_WITH_RELATIONS, ALL
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from tastypie import fields
from .dynamic import *
from cartoview.app_manager.api import rest_api


class BaseCommentResource(ModelResource):
    user = fields.DictField(readonly=True)
    app_instance = fields.ForeignKey(AppInstanceResource, 'app_instance')

    def save(self, bundle, skip_errors=False):
        bundle.obj.user = bundle.request.user
        return super(BaseCommentResource, self).save(bundle, skip_errors)

    def dehydrate_user(self, bundle):
        return dict(username=bundle.obj.user.username, avatar=avatar_url(bundle.obj.user, 60))


_comments_resource_cache = {}


def create_comment_resource(layer_name):
    if layer_name in _comments_resource_cache:
        return _comments_resource_cache[layer_name]
    model = create_comment_model(layer_name)

    class Meta:
        queryset = model.objects.all()
        filtering = {"app_instance": ALL_WITH_RELATIONS,
                     "feature": ALL}
        can_edit = True
        authorization = Authorization()

    resource_attrs = {
        'Meta': Meta,
    }
    resource = type(layer_name, (BaseCommentResource,), resource_attrs)
    rest_api.register(resource())
