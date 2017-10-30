import json

from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from . import APP_NAME
from .decorators import methods_permission
from .dynamic import AttachmentManager, AttachmentSerializer, Tag, db


def index(request):
    return render(request, template_name="%s/index.html" % APP_NAME)


class AttachmentApi(object):
    def __init__(self):
        self.serializer = AttachmentSerializer()
        self.common_allowed_filters = ['tags', 'username', 'feature_id']

    def build_query_filters(self, get_filters):
        main_query = ['queryset = model.select()']
        sub_filters = []
        tags = get_filters.getlist('tags', None)
        if tags:
            main_query.append(
                "join(Tag, on=((Tag.object_id == model.id) & (Tag.object_type == 'attachment_%s_%s' % (layername,attachment_type)) & Tag.tag << get_filters.getlist('tags'))).switch(Tag)")
        for filt in get_filters:
            if filt != 'tags':
                sub_filters.append("model.username=='%s'" % get_filters[filt])
        if sub_filters:
            sub_filter_query = "&".join(sub_filters)
            where_sub_filter_query = "where(%s)" % sub_filter_query
            main_query.append(where_sub_filter_query)
        return ".".join(main_query)

    @method_decorator(methods_permission)
    def attachments_list_create(self, request, layername, attachment_type):
        try:
            request_method = request.method
            get_filters = request.GET
            attachment_obj = AttachmentManager(str(layername))
            model = attachment_obj.create_comment_model() if attachment_type \
                == 'comment' else attachment_obj.create_file_model()
            if request_method == "GET":
                if get_filters and 'tags' in get_filters:
                    exec(self.build_query_filters(get_filters))
                else:
                    queryset = model.select()
                return HttpResponse(self.serializer.attachment_to_json(
                    queryset, attachment_type,
                    layername, many=True),
                    content_type="application/json")
            elif request_method == "POST":
                data = json.loads(request.body)
                request_tags = data.pop('tags', None)
                data = self.serializer.decode_file_data(
                    data) if attachment_type == "file" else data
                if request_tags and isinstance(request_tags, list):
                    obj = model(**data)
                    obj.save()
                    for tag in request_tags:
                        Tag.create(tag=tag, object=obj)
                else:
                    return HttpResponse(json.dumps({'error': "tags fiels is \
                required as List(array) example ['python','python2']"}),
                                        content_type="application/json")
                new_obj = model.get(model.id == obj.id)
                return HttpResponse(self.serializer.attachment_to_json(
                    new_obj,
                    attachment_type, layername,
                    many=False),
                    content_type="application/json")
            else:
                return HttpResponse("%s Method Not Allowed" % request_method,
                                    status=405)
        except Exception as e:
            return HttpResponse(json.dumps({'error': e.message}),
                                content_type="application/json", status=500)

    @method_decorator(methods_permission)
    def attachments_details_update(self, request, layername, attachment_type,
                                   id):
        layername = str(layername)
        request_method = request.method
        attachment_obj = AttachmentManager(str(layername))
        model = attachment_obj.create_comment_model() if attachment_type == \
            'comment' else attachment_obj.create_file_model()

        model_obj = attachment_obj.get_by_id(model, id)
        if not model_obj:
            return HttpResponse("no object with id %s" % id,
                                status=404)

        if request_method == "GET":
            return HttpResponse(
                self.serializer.attachment_to_json(model_obj, attachment_type,
                                                   layername,
                                                   many=False),
                content_type="application/json")
        elif request_method == "PUT":
            field_value = json.loads(request.body)
            field_value = self.serializer.decode_file_data(
                field_value) if attachment_type == "file" else field_value
            with db.atomic() as txn:
                try:
                    for field, value in field_value.iteritems():
                        if field != "tags":
                            setattr(model_obj, field, value)
                        else:
                            for tag in model_obj.tags:
                                if tag.tag not in value:
                                    tag.delete_instance()
                            new_tags = []
                            for tag in value:
                                tag_obj, created = Tag.get_or_create(
                                    tag=tag, object=model_obj)
                                if created:
                                    new_tags.append(tag_obj)
                            setattr(model_obj, field, new_tags)
                    model_obj.save()
                except:
                    txn.rollback()
            return HttpResponse(self.serializer.attachment_to_json(
                model_obj, attachment_type, layername, many=False),
                status=404)
        elif request_method == "DELETE":
            model_obj.delete_instance()
        else:
            return HttpResponse("%s Method Not Allowed" % request_method,
                                status=405)

    @method_decorator(csrf_exempt)
    @method_decorator(methods_permission)
    def attachments_download(self, request, layername,
                             id):
        layername = str(layername)
        attachment_obj = AttachmentManager(str(layername))
        model = attachment_obj.create_file_model()
        model_obj = attachment_obj.get_by_id(model, id)
        if not model_obj:
            return HttpResponse("no object with id %s" % id,
                                status=404)
        contents = model_obj.file
        name = model_obj.file_name
        response = HttpResponse(contents)
        response['Content-Disposition'] = 'attachment; filename=%s' % (name)
        return response

    def tags_list(self, request):
        queryset = Tag.select(Tag.tag).distinct().dicts()
        tags_list = list(queryset)
        api_result = json.dumps(tags_list)
        return HttpResponse(api_result,
                            content_type="application/json")
