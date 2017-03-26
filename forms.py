import django.forms as forms
from geonode.layers.models import Layer

choices = []
for layer in Layer.objects.all():
    id = layer.id
    name = layer.name
    choices.append((name, name))


class Upload_Form(forms.Form):
    layer = forms.ChoiceField(choices, required=True, widget=forms.Select)
    file = forms.FileField()
    feature = forms.IntegerField(min_value=1, required=True)
