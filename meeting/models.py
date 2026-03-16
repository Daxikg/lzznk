from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext as _
from app01.models import Admin


class meeting(models.Model):
    time = models.DateTimeField(verbose_name='时间', auto_now_add=True)
    meeting = models.TextField(verbose_name='会议主题')
    meeting1 = models.TextField(verbose_name='副标题', blank=True, null=True)
    Contents = models.TextField(verbose_name='议定事项', blank=True, null=True)
    Contents1 = models.TextField(verbose_name='会议内容1', blank=True, null=True)
    Contents2 = models.TextField(verbose_name='会议内容2', blank=True, null=True)
    Contents3 = models.TextField(verbose_name='会议内容3', blank=True, null=True)
    Contents4 = models.TextField(verbose_name='会议内容4', blank=True, null=True)
    Contents5 = models.TextField(verbose_name='会议内容5', blank=True, null=True)
    Contents6 = models.TextField(verbose_name='会议内容6', blank=True, null=True)
    Contents7 = models.TextField(verbose_name='会议内容7', blank=True, null=True)
