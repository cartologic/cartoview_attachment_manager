from django.conf.urls import url, patterns
# Seperate Attachments API
from .views import index, AttachmentApi
api = AttachmentApi()
urlpatterns = patterns('',
                       url(r'^$', index),
                       url(r'^(?P<layername>\w+)/comment$',
                           api.comments_list_create),
                       url(r'^(?P<layername>\w+)/comment/(?P<id>/d+)$',
                           api.comments_list_create),
                       #    url(r'^(?P<layername>\w+)/file(?:/(?P<id>/d+)/)?'),
                       )
#                        url(r'^attachment_manager/file$', upload),
#                        url(r'^attachment_manager/view/files$',
#                             view_all_files),
#                        url(r'^attachment_manager/comment$', comment),
#                        url(r'^attachment_manager/view/comments$',
#                            view_all_Comments),
#                        url(r'^attachment_manager/download/\
#                        (?P<layer_name>\w+)/(?P<id>\d+)$', download_blob,
#                            name='attachment_down'),
