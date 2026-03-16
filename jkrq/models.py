from django.db import models
from django.utils.translation import gettext as _
from app01.models import Admin


class JkrqList(models.Model):
    name = models.TextField(_('姓名'), )
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
    banzu = models.IntegerField(_('班组'), choices=banzu_choices)
    PEOPLE_TYPES = [
        ('JKWH', '健康危害风险人员'),
        ('XNXGJB', '心脑血管疾病风险人员'),
    ]
    people_type = models.CharField(
        max_length=20,
        choices=PEOPLE_TYPES,
        default='JKWH', verbose_name='分类'
    )
    PEOPLE_lEVELS = [
        ('lv4', '高危'),
        ('lv3', '三类'),
        ('lv2', '二类（重点）'),
        ('lv1', '二类'),
        ('lv0', '一类'),
    ]
    people_level = models.CharField(
        max_length=20,
        choices=PEOPLE_lEVELS,
        verbose_name='等级'
    )
    people_height = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='身高')
    people_weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='体重')
    people_bmi = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='体重指数')
    PEOPLE_SMOKES = [
        ('1', '否'),
        ('2', '是'),
    ]
    people_smoke = models.CharField(
        max_length=20, choices=PEOPLE_SMOKES, blank=True, null=True, verbose_name='是否吸烟'
    )
    PEOPLE_BLOOD_FATS = [
        ('1', '异常'),
        ('0', '良好'),
    ]
    people_blood_fat = models.CharField(
        max_length=20, choices=PEOPLE_BLOOD_FATS, blank=True, null=True, verbose_name='血脂异常'
    )
    people_blood_candy = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True, verbose_name='血糖')
    people_blood_high = models.CharField(max_length=3, blank=True, null=True, verbose_name='收缩压')
    people_blood_low = models.CharField(max_length=3, blank=True, null=True, verbose_name='舒张压')
    PEOPLE_CHECK_METHODS = [
        ('DAYLY', '每日监测'),
        ('WEEKLY', '每周监测'),
        ('MONTHLY', '每月监测'),
        ('QUARTER', '每季度监测'),
    ]
    people_check_method = models.CharField(
        max_length=20,
        choices=PEOPLE_CHECK_METHODS,
        verbose_name='维护方式'
    )
    time = models.DateField(blank=True, null=True, verbose_name='时间')

    def __str__(self):
        return self.name


class JkrqList1Log(models.Model):
    people = models.ForeignKey(JkrqList, blank=True, null=True, on_delete=models.CASCADE)
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
    banzu = models.IntegerField(_('班组'), choices=banzu_choices)
    check_date = models.DateField(auto_now_add=True, verbose_name='检测日期')
    people_blood_candy = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True, verbose_name='血糖')
    people_blood_high = models.CharField(max_length=3, blank=True, null=True, verbose_name='收缩压')
    people_blood_low = models.CharField(max_length=3, blank=True, null=True, verbose_name='舒张压')
    people_weight = models.DecimalField(max_digits=4, decimal_places=1, verbose_name='体重')
    people_bmi = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='体重指数')
    pic = models.ImageField(_('血压检测照片'), upload_to='blood/%Y/%m/%d/', max_length=100, blank=True, null=True)

