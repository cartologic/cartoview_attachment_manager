from django.conf.urls import patterns, url

# Seperate Attachments API
from .views import AttachmentApi, index

api = AttachmentApi()
urlpatterns = patterns('',
                       url(r'^$', index),
                       url(r'^(?P<layername>\w+)/(?P<attachment_type>comment|file)$',
                           api.attachments_list_create),
                       url(r'^(?P<layername>\w+)/(?P<attachment_type>comment|file)/(?P<id>\d+)$',
                           api.attachments_details_update))
