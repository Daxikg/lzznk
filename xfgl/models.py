from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext as _
from app01.models import Admin
from django.utils import timezone

from bzrz.models import TeamUser


class Operater(models.Model):
    """
    设备负责人
    """
    name = models.CharField(verbose_name='姓名', max_length=10)  # 负责人姓名
    phone = models.CharField(verbose_name='手机号', max_length=13, blank=True, null=True)  # 手机号
    banzu_choices = (
        (1, "架车班"),
        (2, "轮轴班"),
        (3, "台车班"),
        (4, "内制动班"),
        (5, "外制动班"),
        (6, "车钩班"),
        (7, "探伤班"),
        (8, "调车组"),
        (9, "车体班"),
        (10, "预修班"),
        (12, "信息班"),
        (13, "干部"),
    )
    banzu = models.IntegerField(_('所属班组'), choices=banzu_choices, blank=True, null=True)
    chejian_choices = (
        (1, "检修车间"),
        (2, "设备车间"),
    )
    chejian = models.IntegerField(_('所属车间'), choices=chejian_choices, blank=True, null=True)

    def __str__(self):
        return self.name


class Equipment(models.Model):
    """
        设备表
    """
    device_choices = (
        (1, "消火栓"),
        (2, "灭火器"),
        (3, "喷漆房"),
        (4, "集中供气"),
        (5, "液氧"),
        (6, "丙烷"),
        (7, "乙炔"),
    )
    device = models.IntegerField(_('设备名'), choices=device_choices)  # 设备名
    number = models.CharField(_('设备编号'), max_length=100, blank=True, null=True)  # 设备编号
    user = models.ForeignKey(
        'Operater',
        verbose_name='负责人',
        null=True,
        on_delete=models.SET_NULL,
        related_name='user_equipments'
    )
    banzu_choices = (
        (1, "架车班"),
        (2, "轮轴班"),
        (3, "台车班"),
        (4, "内制动班"),
        (5, "外制动班"),
        (6, "车钩班"),
        (7, "探伤班"),
        (8, "调车组"),
        (9, "车体班"),
        (10, "预修班"),
        (12, "信息班"),
    )
    banzu = models.IntegerField(_('所属班组'), choices=banzu_choices, blank=True, null=True)
    type_choices = (
        (1, "气瓶"),
        (2, "喷漆房"),
        (3, "集中供气"),
        (4, "消防器材"),
    )
    type = models.IntegerField(_('设备类型'), choices=type_choices)  # 设备类型
    inspect_choices = [
        (1, '开工前和完工后点检'),
        (2, '每日巡检'),
        (3, '月度检查'),
    ]
    inspect = models.IntegerField(_('检查方式'), choices=inspect_choices)  # 检查方式

    create_time = models.DateTimeField(verbose_name='创建时间', default=timezone.now)  # 创建时间（自动获取当前时间）
    production_time = models.DateField(verbose_name='生产日期', blank=True, null=True)
    break_choices = (
        (0, "正常"),
        (1, "故障"),
    )
    breakdown = models.IntegerField(verbose_name='是否故障', default=0, choices=break_choices)  # 是否故障
    reason = models.CharField(verbose_name='故障原因', max_length=100, blank=True, null=True, default="")  # 故障原因
    check_date = models.DateTimeField(verbose_name='最近一次检查时间', blank=True, null=True)  # 最近一次检查时间
    check_item1 = models.CharField(verbose_name='点检项目1', max_length=100, blank=True, null=True)  # 点检项目1
    check_item2 = models.CharField(verbose_name='点检项目2', max_length=100, blank=True, null=True)  # 点检项目2
    check_item3 = models.CharField(verbose_name='点检项目3', max_length=100, blank=True, null=True)  # 点检项目3
    check_item4 = models.CharField(verbose_name='点检项目4', max_length=100, blank=True, null=True)  # 点检项目4
    check_item5 = models.CharField(verbose_name='点检项目5', max_length=100, blank=True, null=True)  # 点检项目5
    check_item6 = models.CharField(verbose_name='点检项目6', max_length=100, blank=True, null=True)  # 点检项目6
    check_item7 = models.CharField(verbose_name='点检项目7', max_length=100, blank=True, null=True)  # 点检项目7
    check_item8 = models.CharField(verbose_name='点检项目8', max_length=100, blank=True, null=True)  # 点检项目8
    check_item9 = models.CharField(verbose_name='点检项目9', max_length=100, blank=True, null=True)  # 点检项目9
    check_item10 = models.CharField(verbose_name='点检项目10', max_length=100, blank=True, null=True)  # 点检项目10
    qrcode = models.ImageField(upload_to='qrcodes/', blank=True, null=True)  # 二维码照片


class Equipment_log(models.Model):
    """
        检查记录
    """
    device = models.ForeignKey(Equipment, on_delete=models.CASCADE)  # 设备名
    name = models.ForeignKey(Operater, on_delete=models.CASCADE)  # 操作人员
    create_time = models.DateTimeField(verbose_name='检查时间')  # 检查时间（自动获取当前时间）
    create_time1 = models.DateTimeField(verbose_name='完工检查时间', blank=True, null=True)  # 完工检查时间（自动获取当前时间）
    check_item1 = models.BooleanField(default=False)
    check_item2 = models.BooleanField(default=False)
    check_item3 = models.BooleanField(default=False)
    check_item4 = models.BooleanField(default=False)
    check_item5 = models.BooleanField(default=False)
    check_item6 = models.BooleanField(default=False)
    check_item7 = models.BooleanField(default=False)
    check_item8 = models.BooleanField(default=False)
    check_item9 = models.BooleanField(default=False)
    check_item10 = models.BooleanField(default=False)
    beizhu = models.CharField(verbose_name='备注', max_length=100, blank=True, null=True)  # 备注
    pic1 = models.ImageField(_('点检照片1'), upload_to='inspection/', max_length=100, blank=True, null=True)
    pic2 = models.ImageField(_('点检照片2'), upload_to='inspection/', max_length=100, blank=True, null=True)
    pic3 = models.ImageField(_('点检照片3'), upload_to='inspection/', max_length=100, blank=True, null=True)
