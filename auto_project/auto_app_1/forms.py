from auto_project.auto_app_1.models import ModelC
from django.forms.models import ModelForm


class ModelCForm(forms.ModelForm):
    class Meta:
        model = ModelC
        fields = '__all__'