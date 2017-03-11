from django import forms
from ..models import UploadSkipDays


class SkipDaysForm(forms.ModelForm):

    class Meta:
        model = UploadSkipDays
        fields = "__all__"
