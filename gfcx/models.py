from django.db import models
from django.utils.translation import gettext as _
from app01.models import Admin


class Employee(models.Model):
    name = models.CharField(max_length=100)
    gongzhong = models.CharField(max_length=100, null=True, blank=True)
    gonghao = models.CharField(max_length=50, null=True, blank=True)
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
        (15, "修配日勤"),
        (16, "修车日勤"),
    )
    banzu = models.IntegerField(_('班组'), choices=banzu_choices, null=True, blank=True)
    chejian_choices = (
        (1, "修配车间"),
        (2, "修车车间"),
    )
    chejian = models.IntegerField(_('车间'), choices=chejian_choices, null=True, blank=True)
    created_time = models.DateField()

    def __str__(self):
        return self.name


class DailyScore(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()  # 存储具体的日期，如2025-06-01
    work_score = models.FloatField(default=0)
    study_score = models.FloatField(default=0)
    business_score = models.FloatField(default=0)
    holiday_score = models.FloatField(default=0)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'date')  # 确保每个员工每天只有一条记录
        ordering = ['date']  # 默认按日期排序

    def __str__(self):
        return f"{self.employee.name} - {self.date}"


class Accounting(models.Model):
    name = models.CharField(max_length=100)
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
        (15, "修配日勤"),
        (16, "修车日勤"),
    )
    banzu = models.IntegerField(_('班组'), choices=banzu_choices, null=True, blank=True)
    chejian_choices = (
        (1, "修配车间"),
        (2, "修车车间"),
    )
    chejian = models.IntegerField(_('车间'), choices=chejian_choices, null=True, blank=True)
    gongzhong = models.CharField(max_length=100)
    gonghao = models.CharField(max_length=100)
    year = models.IntegerField(verbose_name='年份')
    month = models.IntegerField(verbose_name='月份')
    total_days = models.IntegerField(verbose_name='打分总天数')
    main_area_days = models.IntegerField(verbose_name='本工区打分天数')
    other_area_days = models.IntegerField(verbose_name='其他工区打分天数')
    base_coefficient = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='个人挂钩基数')
    start_score = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='起始分')
    main_area_score = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='本工区定额所得分')
    main_area_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='本工区定额所得金额')
    other_area_score = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='其他工区定额所得分')
    other_area_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='其他工区定额所得金额')
    status = models.CharField(max_length=50, verbose_name='考核状态')
    remarks = models.TextField(blank=True, verbose_name='不参与积分备注说明')
    created_time = models.DateTimeField(auto_now_add=True)

