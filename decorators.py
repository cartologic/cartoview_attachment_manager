from functools import wraps
from django.http.response import HttpResponse
import json


def methods_permission(view):
    @wraps(view)
    def check(request, *args, **kwargs):
        method = request.method
        if request.user.is_authenticated() or method == "GET":
            return view(request, *args, **kwargs)
        elif not request.user.is_authenticated() and method != "GET":
            return HttpResponse(json.dumps({"error": "Unauthorized"}),
                                status=401)
        else:
            return HttpResponse(json.dumps({"error": "Method Not allowed"}),
                                status=405)
    return check
