from django.conf.urls import url, include
from attachment_manager.views import *

url_patterns = (
    url(r'^attachment_file/$', upload),
    url(r'^attachment_file/view$', view_all_files),
    url(r'^attachment_file/download/(?P<layer_name>\w+)/(?P<id>\d+)$', download_blob,
        name='attachment_down'),
)
