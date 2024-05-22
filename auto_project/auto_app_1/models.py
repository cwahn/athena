from django.db.models import BooleanField


class ModelC(models.Model):
    is_active = BooleanField(null=False, default=False, blank=False, verbose_name=Nothing, help_text=Nothing)