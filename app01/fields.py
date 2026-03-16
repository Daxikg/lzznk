# 新建fields.py
from django.db import models
from django.forms import Textarea


class CKEditor5Widget(Textarea):
    template_name = 'widgets/ckeditor5.html'

    class Media:
        css = {'all': []}
        js = ['js/ckeditor.js']  # 确保路径正确


class CKEditor5Field(models.TextField):
    def formfield(self, **kwargs):
        kwargs['widget'] = CKEditor5Widget
        return super().formfield(**kwargs)
