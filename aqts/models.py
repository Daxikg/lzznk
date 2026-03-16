from ckeditor.fields import RichTextField
from django.db import models
from django.utils.translation import gettext as _


class Anquantianshu(models.Model):
    anquanbiaoti = models.TextField(_('安全标题'))
    user = models.TextField(_('发布人'), blank=True, null=True)
    anquanneirong = models.TextField(_('安全内容'), blank=True, null=True)
    anquanfenlei_choices = (
        ("劳动安全", "劳动安全"),
        ("行车安全", "行车安全"),
        ("车辆故障", "车辆故障"),
    )
    anquanfenlei = models.CharField(_('安全分类'), max_length=10, choices=anquanfenlei_choices)
    todaytime = models.DateTimeField(_('日期'), auto_now_add=True)
    file = models.FileField(_('附件'), upload_to='attachment/%Y-%m-%d/', max_length=100, blank=True, null=True)
    chejian_choices = (
        (1, "修配车间"),
        (2, "修车车间"),
    )
    chejian = models.IntegerField(_('车间'), choices=chejian_choices)

    def __str__(self):
        return f"{self.anquanbiaoti} ({self.todaytime})"

