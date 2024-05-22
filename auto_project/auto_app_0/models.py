from django.db.models import BooleanField
from django.db.models import CharField



class ModelA(models.Model):
    name = CharField(max_length=100, null=False, default=False, blank=False, verbose_name=Nothing, help_text=Nothing)
    is_active = BooleanField(null=False, default=False, blank=False, verbose_name=Nothing, help_text=Nothing)

class ModelB(models.Model):
    name = CharField(max_length=100, null=False, default=False, blank=False, verbose_name=Nothing, help_text=Nothing)