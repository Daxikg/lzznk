from django.db import models


class Inventory(models.Model):
    old_axle_D_a = models.IntegerField('本段旧轴D', default=0)
    old_axle_E_a = models.IntegerField('本段旧轴E', default=0)
    old_wheel_D_a = models.IntegerField('本段旧轮D', default=0)
    old_wheel_E_a = models.IntegerField('本段旧轮E', default=0)
    new_axle_D_a = models.IntegerField('本段新轴D', default=0)
    new_axle_E_a = models.IntegerField('本段新轴E', default=0)
    new_wheel_D_a = models.IntegerField('本段新轮D', default=0)
    new_wheel_E_a = models.IntegerField('本段新轮E', default=0)
    old_axle_D_b = models.IntegerField('贵厂旧轴D', default=0)
    old_axle_E_b = models.IntegerField('贵厂旧轴E', default=0)
    old_wheel_D_b = models.IntegerField('贵厂旧轮D', default=0)
    old_wheel_E_b = models.IntegerField('贵厂旧轮E', default=0)
    new_axle_D_b = models.IntegerField('贵厂新轴D', default=0)
    new_axle_E_b = models.IntegerField('贵厂新轴E', default=0)
    new_wheel_D_b = models.IntegerField('贵厂新轮D', default=0)
    new_wheel_E_b = models.IntegerField('贵厂新轮E', default=0)
    old_axle_D_c = models.IntegerField('成都北旧轴D', default=0)
    old_axle_E_c = models.IntegerField('成都北旧轴E', default=0)
    old_wheel_D_c = models.IntegerField('成都北旧轮D', default=0)
    old_wheel_E_c = models.IntegerField('成都北旧轮E', default=0)
    new_axle_D_c = models.IntegerField('成都北新轴D', default=0)
    new_axle_E_c = models.IntegerField('成都北新轴E', default=0)
    new_wheel_D_c = models.IntegerField('成都北新轮D', default=0)
    new_wheel_E_c = models.IntegerField('成都北新轮E', default=0)


class InventoryRecord(models.Model):
    OPERATION_TYPES = [
        ('本段调出', '本段调出'),
        ('调入本段', '调入本段'),
        ('检修新品消耗', '检修新品消耗'),
        ('报废', '报废'),
    ]
    FACTORY_CHOICES = [
        ('贵厂', '贵厂'),
        ('成都北', '成都北'),
    ]
    factory = models.CharField('段名称', max_length=20, choices=FACTORY_CHOICES, blank=True, null=True)
    operation_type = models.CharField('操作类型', max_length=20, choices=OPERATION_TYPES)
    record_date = models.DateField('记录日期')
    old_axle_D_a = models.IntegerField('旧轴D', default=0)
    old_axle_E_a = models.IntegerField('旧轴E', default=0)
    old_wheel_D_a = models.IntegerField('旧轮D', default=0)
    old_wheel_E_a = models.IntegerField('旧轮E', default=0)
    new_axle_D_a = models.IntegerField('新轴D', default=0)
    new_axle_E_a = models.IntegerField('新轴E', default=0)
    new_wheel_D_a = models.IntegerField('新轮D', default=0)
    new_wheel_E_a = models.IntegerField('新轮E', default=0)
    old_axle_D_b = models.IntegerField('旧轴D', default=0)
    old_axle_E_b = models.IntegerField('旧轴E', default=0)
    old_wheel_D_b = models.IntegerField('旧轮D', default=0)
    old_wheel_E_b = models.IntegerField('旧轮E', default=0)
    new_axle_D_b = models.IntegerField('新轴D', default=0)
    new_axle_E_b = models.IntegerField('新轴E', default=0)
    new_wheel_D_b = models.IntegerField('新轮D', default=0)
    new_wheel_E_b = models.IntegerField('新轮E', default=0)
    old_axle_D_c = models.IntegerField('旧轴D', default=0)
    old_axle_E_c = models.IntegerField('旧轴E', default=0)
    old_wheel_D_c = models.IntegerField('旧轮D', default=0)
    old_wheel_E_c = models.IntegerField('旧轮E', default=0)
    new_axle_D_c = models.IntegerField('新轴D', default=0)
    new_axle_E_c = models.IntegerField('新轴E', default=0)
    new_wheel_D_c = models.IntegerField('新轮D', default=0)
    new_wheel_E_c = models.IntegerField('新轮E', default=0)
