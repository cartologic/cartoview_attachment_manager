from django.conf.urls import patterns, url

# Seperate Attachments API
from .views import AttachmentApi, index

api = AttachmentApi()
urlpatterns = patterns('',
                       url(r'^$', index),
                       url(r'^(?P<layername>\w+)/comment$',
                           api.comments_list_create),
                       url(r'^(?P<layername>\w+)/comment/(?P<id>\d+)$',
                           api.comments_details_update))
