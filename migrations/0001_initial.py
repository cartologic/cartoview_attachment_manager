# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app_manager', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('feature', models.PositiveIntegerField(null=True, blank=True)),
                ('identifier', models.CharField(max_length=256, null=True, blank=True)),
                ('comment', models.TextField()),
                ('app_instance', models.ForeignKey(related_name='attachment_comment', blank=True, to='app_manager.AppInstance', null=True)),
                ('user', models.ForeignKey(related_name='attachment_comment', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('feature', models.PositiveIntegerField(null=True, blank=True)),
                ('identifier', models.CharField(max_length=256, null=True, blank=True)),
                ('rate', models.PositiveSmallIntegerField()),
                ('app_instance', models.ForeignKey(related_name='attachment_rating', blank=True, to='app_manager.AppInstance', null=True)),
                ('user', models.ForeignKey(related_name='attachment_rating', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
