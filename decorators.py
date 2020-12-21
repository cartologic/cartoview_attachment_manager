from functools import wraps
from django.http import HttpResponse
import json
from geonode.layers.models import Layer


def methods_permission(view):
    @wraps(view)
    def check(request, *args, **kwargs):
        method = request.method
        if request.user.is_authenticated or method == "GET":
            return view(request, *args, **kwargs)
        elif not request.user.is_authenticated() and method != "GET":
            return HttpResponse(json.dumps({"error": "Unauthorized"}),
                                status=401)
        else:
            return HttpResponse(json.dumps({"error": "Method Not allowed"}),
                                status=405)
    return check


def layer_exist(view):
    @wraps(view)
    def check(request, *args, **kwargs):
        layername = kwargs.get('layername')
        layers = Layer.objects.filter(typename__contains=layername)
        if layers.count() > 0:
            return view(request, *args, **kwargs)
        else:
            return HttpResponse(json.dumps({"error": "No Layer with this name "}),
                                status=405)
    return check
