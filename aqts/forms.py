from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from . import models
from .models import Anquantianshu


class AnquantianshuForm(forms.ModelForm):
    class Meta:
        model = Anquantianshu
        fields = ['anquanbiaoti', 'user', 'anquanneirong', 'anquanfenlei', 'file']
        widgets = {
            'anquanneirong': CKEditorUploadingWidget(),
            'anquanbiaoti': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'user': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
