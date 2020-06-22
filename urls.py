from django.urls import path, re_path

# Seperate Attachments API
from .views import AttachmentApi, index

api = AttachmentApi()
urlpatterns = [
    path('', index),
    re_path(r'^(?P<layername>\w+)/(?P<attachment_type>comment|file)$',
        api.attachments_list_create, name="attachment_list"),
    re_path(r'^(?P<layername>\w+)/(?P<attachment_type>comment|file)/(?P<id>\d+)$',
        api.attachments_details_update, name="attachment_details"),
    path('<str:layername>/<int:id>/download', api.attachments_download, name="attachment_download"),
    path('tags', api.tags_list, name="tags_list")
]
