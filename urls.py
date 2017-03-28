from django.conf.urls import url, include
from .views import *

url_patterns = (
    url(r'^attachment_manager/$', upload),
    url(r'^attachment_manager/view/files$', view_all_files),
    url(r'^attachment_manager/comment$', comment),
    url(r'^attachment_manager/view/comments$', view_all_Comments),
    url(r'^attachment_manager/download/(?P<layer_name>\w+)/(?P<id>\d+)$', download_blob,
        name='attachment_down'),
)
