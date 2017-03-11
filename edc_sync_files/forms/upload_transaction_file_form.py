from django import forms
from ..models import UploadTransactionFile


class UploadTransactionFileForm(forms.ModelForm):

    class Meta:
        model = UploadTransactionFile
        fields = "__all__"
