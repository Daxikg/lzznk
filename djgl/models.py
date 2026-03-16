from ckeditor.fields import RichTextField
from django.db import models
from django.utils.translation import gettext as _


class dangyuan(models.Model):
    banzu_choices = (
        (1, "架车班党支部"),
        (2, "轮轴班党支部"),
        (3, "台车班党支部"),
        (4, "内制动班党支部"),
        (5, "外制动班党支部"),
        (6, "车钩班党支部"),
        (7, "探伤班党支部"),
        (8, "调车组党支部"),
        (9, "车体班党支部"),
        (10, "预修班党支部"),
        (12, "信息班党支部"),
    )
    banzu = models.IntegerField(_('班组'), choices=banzu_choices)
    name = models.TextField(_('姓名'), )
    gender_choices = (
        (1, "男"),
        (2, "女")
    )
    gender = models.IntegerField(_('性别'), choices=gender_choices)
    retire_choices = (
        (1, "在职"),
        (2, "退休"),
    )
    retire = models.IntegerField(_('在职/退休'), default=1, choices=retire_choices)
    birth = models.DateField(_('出生年月'), blank=True, null=True)
    join = models.DateField(_('入党时间'), blank=True, null=True)
    position = models.TextField(_('职务'), blank=True, null=True)
    number = models.TextField(_('联系电话'), blank=True, null=True)
    jiangcheng = models.TextField(_('奖惩情况'), blank=True, null=True)
    nationality = models.TextField(_('民族'), blank=True, null=True)
    zerengang = models.TextField(_('责任岗'), blank=True, null=True)
    zerenqu = models.TextField(_('责任区'), blank=True, null=True)
    time = models.DateField(_('工作时间'), blank=True, null=True)
    pic = models.ImageField(_('党员照片'), max_length=100, blank=True, null=True)


class dangyuanjifen(models.Model):
    user = models.ForeignKey('dangyuan', on_delete=models.CASCADE)
    banzu_choices = (
        (1, "架车班党支部"),
        (2, "轮轴班党支部"),
        (3, "台车班党支部"),
        (4, "内制动班党支部"),
        (5, "外制动班党支部"),
        (6, "车钩班党支部"),
        (7, "探伤班党支部"),
        (8, "预修班党支部"),
        (9, "车体班党支部"),
        (10, "调车组党支部"),
        (12, "信息班党支部"),
    )
    banzu = models.IntegerField(_('班组'), choices=banzu_choices)
    jifen = models.IntegerField(_('党员积分'), blank=True, null=True)
    time = models.DateField(_('时间'), blank=True, null=True)
    zzsz = models.CharField(_('政治素质'), max_length=200, blank=True, null=True)
    ywjn = models.CharField(_('业务技能'), max_length=200, blank=True, null=True)
    gzyj = models.CharField(_('工作业绩'), max_length=200, blank=True, null=True)
    lxqz = models.CharField(_('联系群众'), max_length=200, blank=True, null=True)
    jfxd = models.CharField(_('加分项点'), max_length=200, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'time']),
        ]


class dangyuancgjq(models.Model):
    user = models.ForeignKey('dangyuan', on_delete=models.CASCADE)
    banzu_choices = (
        (1, "架车班党支部"),
        (2, "轮轴班党支部"),
        (3, "台车班党支部"),
        (4, "内制动班党支部"),
        (5, "外制动班党支部"),
        (6, "车钩班党支部"),
        (7, "探伤班党支部"),
        (8, "预修班党支部"),
        (9, "车体班党支部"),
        (10, "调车组党支部"),
        (12, "信息班党支部"),

    )
    banzu = models.IntegerField(_('班组'), choices=banzu_choices)
    year = models.IntegerField(_('年份'))
    quarter_choices = (
        (1, "一季度"),
        (2, "二季度"),
        (3, "三季度"),
        (4, "四季度"),
    )
    quarter = models.IntegerField(_('季度'), choices=quarter_choices)
    zerengang_choices = (
        (1, "先锋岗"),
        (2, "达标岗"),
        (3, "警示岗"),
    )
    zerengang = models.IntegerField(_('责任岗'), choices=zerengang_choices, blank=True, null=True)
    zerenqu_choices = (
        (1, "红旗区"),
        (2, "达标区"),
        (3, "警示区"),
    )
    zerenqu = models.IntegerField(_('责任区'), choices=zerenqu_choices, blank=True, null=True)


class dangyuanindex(models.Model):
    user = models.ForeignKey('dangyuan', on_delete=models.CASCADE)
    chejian_choices = (
        (1, "修配车间"),
        (2, "修车车间"),
    )
    chejian = models.IntegerField(_('车间'), choices=chejian_choices)
    year = models.IntegerField(_('年份'))
    quarter_choices = (
        (1, "一季度"),
        (2, "二季度"),
        (3, "三季度"),
        (4, "四季度"),
    )
    quarter = models.IntegerField(_('季度'), choices=quarter_choices)
    hongqiqu = models.TextField(_('红旗区'), blank=True, null=True)
    dabiaoqu = models.TextField(_('达标区'), blank=True, null=True)
    jingshiqu = models.TextField(_('警示区'), blank=True, null=True)
    xianfenggang = models.TextField(_('先锋岗'), blank=True, null=True)
    dabiaogang = models.TextField(_('达标岗'), blank=True, null=True)
    jingshigang = models.TextField(_('警示岗'), blank=True, null=True)
    siyoudangyuan = models.TextField(_('四优党员'), blank=True, null=True)
    anquanzhixing = models.TextField(_('安全之星'), blank=True, null=True)


class dangjiantext(models.Model):
    banzu_choices = (
        (1, "架车班党支部"),
        (2, "轮轴班党支部"),
        (3, "台车班党支部"),
        (4, "内制动班党支部"),
        (5, "外制动班党支部"),
        (6, "车钩班党支部"),
        (7, "探伤班党支部"),
        (8, "预修班党支部"),
        (9, "车体班党支部"),
        (10, "调车组党支部"),
        (12, "信息班党支部"),
        (15, "修配党支部"),
        (16, "修车党支部"),
    )
    banzu = models.IntegerField(_('班组'), choices=banzu_choices)
    neirong = RichTextField(_('其他公示'), blank=True, null=True)
    jieshao = RichTextField(_('党支部介绍'), blank=True, null=True)

