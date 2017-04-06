from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .forms import Upload_Form, Comment_Form
from .dynamic import create_file_model, create_comment_model
from geonode.layers.models import Layer
from .dynamic import check_table_exists


def upload(request):
    form = Upload_Form()
    if request.method == 'POST':
        form = Upload_Form(request.POST or None, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            model = create_file_model('File', form.cleaned_data['layer'], app_label='fake_app',
                                      module='fake_project.fake_app.no_models')
            model.objects.create(file=file.read(), file_name=file.name, user=request.user,
                                 feature=form.cleaned_data['feature'])
        return HttpResponseRedirect('/attachment_manager/view/files')
    return render(request, template_name='attachment_manager/test.html', context={'form': form})


def comment(request):
    form = Comment_Form()
    if request.method == 'POST':
        form = Comment_Form(request.POST or None)
        if form.is_valid():
            comment = form.cleaned_data['comment']
            model = create_comment_model('Comment', form.cleaned_data['layer'], app_label='fake_app',
                                         module='fake_project.fake_app.no_models')
            obj = model.objects.create(comment=comment, user=request.user, feature=form.cleaned_data['feature'])
        return HttpResponseRedirect('/attachment_manager/view/comments')
    return render(request, template_name='attachment_manager/test1.html', context={'form': form})


def view_all_files(request):
    result = []
    for layer in Layer.objects.all():
        if check_table_exists(table_name='attachment_manager_file_%s' % layer.name):
            model = create_file_model('File', layer.name, app_label='fake_app',
                                      module='fake_project.fake_app.no_models')
            if model.objects.all().count() > 0:
                result.append({'%s' % layer.name: model.objects.all()})
    return render(request, template_name='attachment_manager/view.html', context={'files': result, "len": len(result)})


def view_all_Comments(request):
    from .dynamic import create_comment_resource
    result = []
    for layer in Layer.objects.all():
        if check_table_exists(table_name='attachment_manager_comment_%s' % layer.name):
            model = create_comment_model('Comment', layer.name, app_label='fake_app',
                                         module='fake_project.fake_app.no_models')
            if model.objects.all().count() > 0:
                result.append({'%s' % layer.name: model.objects.all()})
    return render(request, template_name='attachment_manager/view1.html',
                  context={'comments': result, "len": len(result)})


def download_blob(request, layer_name, id):
    model = create_file_model('File', layer_name, app_label='fake_app',
                              module='fake_project.fake_app.no_models')
    obj = model.objects.get(id=id)
    contents = obj.file
    name = obj.file_name
    response = HttpResponse(contents)
    response['Content-Disposition'] = 'attachment; filename=%s' % (name)
    return response


@api_view(['GET', 'POST'])
def hello_world(request, layer_name):
    if request.method == 'POST':
        return Response({"message": "Got some data!", "data": request.data})
    return Response({"message": "Hello, world!"})


from .serializers import comment_serializer


class CommentList(generics.ListCreateAPIView):
    def get_queryset(self):
        model = self.get_model()
        return model.objects.all()

    def get_serializer_class(self):
        model = self.get_model()
        serializer = comment_serializer(model)
        return serializer

    def get_model(self):
        layer_name = self.kwargs['layer']
        print layer_name
        model = create_comment_model('Comment_{0}'.format(layer_name), layer_name, app_label='{0}'.format(layer_name),
                                     module='{0}_project.{0}.{0}_models'.format(layer_name))
        return model
