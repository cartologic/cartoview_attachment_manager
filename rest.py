from django.views.decorators.csrf import csrf_exempt
from cartoview.app_manager.models import AppInstance

from .dynamic import create_comment_model


@csrf_exempt
def post_comment(request):
    if request.method == 'POST':
        comment = request.POST.get('comment', None)
        feature = request.POST.get('feature', None)
        app_instance = AppInstance.objects.get(id=request.POST.get('app_id', None))
        user = request.user
        layer_name = request.POST.get('layer_name', None)
        model = create_comment_model('Comment', layer_name, app_label='fake_app',
                                     module='fake_project.fake_app.no_models')
        model.objects.create(comment=comment, app_instance=app_instance, user=user, feature=feature)
