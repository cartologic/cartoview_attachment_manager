from cartoview.app_manager.models import AppInstance
from django.contrib.gis.db import models
from django.conf import settings


class BasicModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="attachment_%(class)s")
    app_instance = models.ForeignKey(AppInstance, related_name="attachment_%(class)s", blank=True, null=True)
    feature = models.PositiveIntegerField(blank=True, null=True)
    identifier = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        abstract = True


class Comment(BasicModel):
    comment = models.TextField()

    def __unicode__(self):
        return self.comment


class Rating(BasicModel):
    rate = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return self.rate

# class File(BasicModel):
#     file = models.BinaryField()
#     file_name = models.CharField(max_length=150)
#     is_image = models.BooleanField(default=False)
#
#     def __unicode__(self):
#         return self.file_name
