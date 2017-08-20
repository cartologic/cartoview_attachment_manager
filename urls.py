from django.conf.urls import patterns, url

# Seperate Attachments API
from .views import AttachmentApi, index

api = AttachmentApi()
urlpatterns = patterns('',
                       url(r'^$', index),
                       url(r'^(?P<layername>\w+)/(?P<attachment_type>comment|file)$',
                           api.attachments_list_create, name="attachment_list"),
                       url(r'^(?P<layername>\w+)/(?P<attachment_type>comment|file)/(?P<id>\d+)$',
                           api.attachments_details_update, name="attachment_details"),
                       url(r'^(?P<layername>\w+)/file/(?P<id>\d+)/download$',
                           api.attachments_download, name="attachment_download")
                       )
