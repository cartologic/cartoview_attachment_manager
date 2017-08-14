from django.shortcuts import render
from . import APP_NAME


def index(request):
    return render(request, template_name="%s/index.html" % APP_NAME)
