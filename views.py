import json
from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from . import APP_NAME
from .dynamic import AttachmentManager, Tag


def index(request):
    return render(request, template_name="%s/index.html" % APP_NAME)


class AttachmentApi(object):
    @method_decorator(csrf_exempt)
    def comments_list_create(self, request, layername):
        try:
            request_method = request.method
            attachment_obj = AttachmentManager(str(layername))
            model = attachment_obj.create_comment_model()
            if request_method == "GET":
                queryset = model.select()
                return HttpResponse(AttachmentManager.to_json(queryset,
                                                              many=True),
                                    content_type="application/json")
            elif request_method == "POST":
                data = json.loads(request.body)
                request_tags = data.pop('tags', None)
                print request_tags and isinstance(request_tags, list)
                if request_tags and isinstance(request_tags, list):
                    obj = model(**data)
                    obj.save()
                    for tag in request_tags:
                        Tag.create(tag=tag, object=obj)
                else:
                    return HttpResponse(json.dumps({'error': "tags fiels is \
                required as List(array) example ['python','python2']"}),
                                        content_type="application/json")
                new_comment = model.get(model.id == obj.id)
                return HttpResponse(AttachmentManager.to_json(new_comment, many=False),
                                    content_type="application/json")
        except Exception as e:
            return HttpResponse(json.dumps({'error': e.message}),
                                content_type="application/json")
