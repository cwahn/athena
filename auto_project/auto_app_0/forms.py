from auto_project.auto_app_0.models import ModelA
from django.forms.models import ModelForm
from auto_project.auto_app_0.models import ModelB



class ModelAForm(forms.ModelForm):
    class Meta:
        model = ModelA
        fields = '__all__'

class ModelBForm(forms.ModelForm):
    class Meta:
        model = ModelB
        fields = '__all__'