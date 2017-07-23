from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
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
            model = create_file_model(form.cleaned_data['layer'])
            model.objects.create(
                file=file.read(),
                file_name=file.name,
                user=request.user,
                feature=form.cleaned_data['feature'])
        return HttpResponseRedirect('/attachment_manager/view/files')
    return render(
        request,
        template_name='attachment_manager/test.html',
        context={
            'form': form})


def comment(request):
    form = Comment_Form()
    if request.method == 'POST':
        form = Comment_Form(request.POST or None)
        if form.is_valid():
            comment = form.cleaned_data['comment']
            model = create_comment_model(form.cleaned_data['layer'])
            obj = model.objects.create(
                comment=comment,
                user=request.user,
                feature=form.cleaned_data['feature'])
            # return HttpResponseRedirect('/attachment_manager/view/comments')
    return render(
        request,
        template_name='attachment_manager/test1.html',
        context={
            'form': form})


def view_all_files(request):
    result = []
    for layer in Layer.objects.all():
        if check_table_exists(
                table_name='attachment_manager_file_%s' %
                layer.name):
            model = create_file_model(layer.name)
            if model.objects.all().count() > 0:
                result.append({'%s' % layer.name: model.objects.all()})
    return render(
        request,
        template_name='attachment_manager/view.html',
        context={
            'files': result,
            "len": len(result)})


def view_all_Comments(request):
    result = []
    for layer in Layer.objects.all():
        if check_table_exists(
                table_name='attachment_manager_comment_%s' %
                layer.name):
            model = create_comment_model(layer.name)
            if model.objects.all().count() > 0:
                result.append({'%s' % layer.name: model.objects.all()})
    return render(request, template_name='attachment_manager/view1.html',
                  context={'comments': result, "len": len(result)})


def download_blob(request, layer_name, id):
    model = create_file_model(layer_name)
    obj = model.objects.get(id=id)
    contents = obj.file
    name = obj.file_name
    response = HttpResponse(contents)
    response['Content-Disposition'] = 'attachment; filename=%s' % (name)
    return response
