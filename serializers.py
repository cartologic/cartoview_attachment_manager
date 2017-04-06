from rest_framework import serializers
from django.db import  models
from .dynamic import create_comment_model
from cartoview.app_manager.models import AppInstance
from geonode.people.models import Profile


def create_comment_serializer(name, model):
    class SnippetSerializer(serializers.Serializer):
        id = serializers.IntegerField(read_only=True)
        created_at = serializers.DateTimeField(read_only=True)
        updated_at = serializers.DateTimeField(read_only=True)

        def create(self, validated_data):
            """
            Create and return a new `Snippet` instance, given the validated data.
            """
            file = validated_data['file']
            file_data = file.read()
            return model.objects.create(**validated_data)

        def update(self, instance, validated_data):
            """
            Update and return an existing `Snippet` instance, given the validated data.
            """
            instance.title = validated_data.get('title', instance.title)
            instance.code = validated_data.get('code', instance.code)
            instance.linenos = validated_data.get('linenos', instance.linenos)
            instance.language = validated_data.get('language', instance.language)
            instance.style = validated_data.get('style', instance.style)
            instance.save()
            return instance


def comment_serializer(s_model):
    class CreateCommentSerializer(serializers.ModelSerializer):
        class Meta:
            model = s_model
            fields = '__all__'
            read_only_fields = ('user',)

        def create(self, validated_data):
            user = 1000
            request = self.context.get("request")
            if request and hasattr(request, "user"):
                user = request.user
            else:
                user = Profile.objects.get(id=user)
            obj = s_model.objects.create(user=user, **validated_data)
            return obj

    return CreateCommentSerializer
