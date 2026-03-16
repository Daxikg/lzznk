from django.db import models
from django.utils.translation import gettext as _
from django.utils import timezone

from bzrz.models import TeamUser


class Circulates(models.Model):
    """
        文件传阅
    """
    classification_choices = (
        ('安全管理', '安全管理'),
        ('设备管理', '设备管理'),
        ('生产管理', '生产管理'),
        ('特种设备', '特种设备'),
        ('消防安全', '消防安全'),
        ('网络安全', '网络安全'),
        ('综合事务', '综合事务'),
        ('技术管理', '技术管理'),
        ('产品质量', '产品质量'),
    )
    classification = models.CharField(_('传阅分类'), max_length=50, choices=classification_choices)
    title = models.CharField(_('传阅名称'), max_length=100)
    name = models.CharField(_('发布人'), max_length=100)
    key_remindertitle = models.CharField(_('重点提示'), max_length=100, blank=True, null=True)
    chejian_choices = (
        (1, "修配车间"),
        (2, "修车车间"),
    )
    chejian = models.IntegerField(_('车间'), choices=chejian_choices)
    create_time = models.DateTimeField(verbose_name='发布日期', default=timezone.now)  # 创建时间（自动获取当前时间）
    status_choices = (
        (0, "正在传阅"),
        (1, "已关闭传阅"),
    )
    status = models.IntegerField(verbose_name='是否传阅', default=0, choices=status_choices)


class CirculateAttachment(models.Model):
    circulate = models.ForeignKey(Circulates, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(_('附件'), upload_to='wjcy/', max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)


def get_photo_path(instance, filename):
    # 格式：2025-07-05-name
    date_str = timezone.now().strftime('%Y-%m-%d')
    name = instance.user.name
    return f'wjcy/{date_str}-{name}.jpg'


class CirculateReads(models.Model):
    circulate = models.ForeignKey(Circulates, on_delete=models.CASCADE)
    user = models.ForeignKey(TeamUser, related_name='circulatephoto', on_delete=models.CASCADE)
    photo = models.FileField(_('照片'), upload_to=get_photo_path, max_length=100)
    beizhu = models.CharField(_('缺席原因'), max_length=100, blank=True, null=True)
    read = models.BooleanField(default=False)
    photo_at = models.DateTimeField(blank=True, null=True)

