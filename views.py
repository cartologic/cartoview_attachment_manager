from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .forms import Upload_Form
from .dynamic import create_file_model
from geonode.layers.models import Layer


# Create your views here.
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
        return HttpResponseRedirect('/attachment_file/view')
    return render(request, template_name='attachment_manager/test.html', context={'form': form})


def view_all_files(request):
    result = []
    from .dynamic import check_table_exists
    for layer in Layer.objects.all():
        if check_table_exists(table_name='attachment_manager_file_%s' % layer.name):
            model = create_file_model('File', layer.name, app_label='fake_app',
                                      module='fake_project.fake_app.no_models')
            if model.objects.all().count() > 0:
                result.append({'%s' % layer.name: model.objects.all()})
    return render(request, template_name='attachment_manager/view.html', context={'files': result, "len": len(result)})


def download_blob(request, layer_name, id):
    model = create_file_model('File', layer_name, app_label='fake_app',
                              module='fake_project.fake_app.no_models')
    obj = model.objects.get(id=id)
    contents = obj.file
    name = obj.file_name
    response = HttpResponse(contents)
    response['Content-Disposition'] = 'attachment; filename=%s' % (name)
    return response
