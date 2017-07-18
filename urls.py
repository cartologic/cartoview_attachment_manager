from django.conf.urls import url, include, patterns
from .views import *
from tastypie.api import Api
from cartoview.urls import urlpatterns as carto_urls
from .rest import *
#Seperate Attachments API
attachments_api = Api(api_name='attachments')
attachments_api.register(CommentResource())
attachments_api.register(FileResource())
urlpatterns = patterns('',
                       url(r'^attachment_manager/file$', upload),
                       url(r'^attachment_manager/view/files$', view_all_files),
                       url(r'^attachment_manager/comment$', comment),
                       url(r'^attachment_manager/view/comments$', view_all_Comments),
                       url(r'^attachment_manager/download/(?P<layer_name>\w+)/(?P<id>\d+)$', download_blob,
                           name='attachment_down'),
                       )

carto_urls += patterns('',
                       url(r'^REST/', include(attachments_api.urls)), )
