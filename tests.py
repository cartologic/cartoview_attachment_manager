from django.test import TestCase
from dynamic import *
from geonode.people.models import Profile
import os


# Create your tests here.
class FileTest(TestCase):
    def setUp(self):
        data_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(data_path, 'image.png')
        with open(file_path) as f:
            file = f.read()
        model = create_file_model('hisham')
        model.objects.create(file=file, file_name=os.path.basename(file_path), is_image=True,
                             user=Profile.objects.all()[0])

    def test_object_created(self):
        """Animals that can speak are correctly identified"""
        data_path = os.path.dirname(os.path.realpath(__file__))
        model = create_file_model('hisham')
        obj = model.objects.all().last()
        with open(os.path.join(data_path, 'output_' + obj.file_name), 'w+') as f:
            f.write(obj.file)

        self.assertEqual(os.path.exists(os.path.join(data_path, 'output_' + obj.file_name), True))
