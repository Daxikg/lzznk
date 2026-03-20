from django.db import models


class Device(models.Model):
    """设备模型"""
    STATUS_CHOICES = [
        ('running', '运行中'),
        ('fault', '故障'),
        ('offline', '离线'),
    ]

    TYPE_CHOICES = [
        ('grind', '磨合设备'),
        ('detect', '检测设备'),
        ('unload', '退卸设备'),
        ('rust', '除锈设备'),
        ('flaw', '探伤设备'),
        ('oil', '涂油设备'),
        ('bolt', '紧固设备'),
        ('press', '压装设备'),
        ('measure', '测量设备'),
        ('crane', '天车设备'),
        ('lathe', '车轮车床'),
        ('protect', '防护装置'),
        ('forklift', '货叉装置'),
        ('stacker', '堆垛系统'),
        ('warehouse', '立体库'),
        # 保留旧类型兼容
        ('platform', '平台设备'),
        ('conveyor', '传输设备'),
        ('cabinet', '控制设备'),
        ('room', '防护设施'),
        ('power', '动力设备'),
    ]

    device_id = models.CharField('设备编号', max_length=20, unique=True)
    name = models.CharField('设备名称', max_length=100)
    area = models.CharField('所属区域', max_length=50)
    device_type = models.CharField('设备类型', max_length=30, choices=TYPE_CHOICES, default='measure')
    description = models.CharField('设备描述', max_length=200, blank=True, default='')

    # 状态相关
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='offline')
    fault_time = models.DateTimeField('故障发生时间', null=True, blank=True)

    # 位置信息（用于大屏展示）
    pos_x = models.IntegerField('X坐标', default=0)
    pos_y = models.IntegerField('Y坐标', default=0)
    pos_width = models.IntegerField('宽度', default=100)
    pos_height = models.IntegerField('高度', default=60)

    # 立体库专用字段
    capacity = models.IntegerField('总容量', null=True, blank=True)
    used = models.IntegerField('已使用', null=True, blank=True)

    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '设备'
        verbose_name_plural = '设备'
        ordering = ['device_id']

    def __str__(self):
        return f"{self.device_id} - {self.name}"

    @property
    def computed_status(self):
        """计算实际状态（判断是否为长时间故障）"""
        from django.utils import timezone
        if self.status == 'fault' and self.fault_time:
            fault_duration = timezone.now() - self.fault_time
            # 超过2小时算长时间故障
            if fault_duration.total_seconds() > 2 * 60 * 60:
                return 'longFault'
        return self.status


class DeviceArea(models.Model):
    """区域配置"""
    name = models.CharField('区域名称', max_length=50, unique=True)
    pos_x = models.IntegerField('X坐标', default=0)
    pos_y = models.IntegerField('Y坐标', default=0)
    width = models.IntegerField('宽度', default=200)
    height = models.IntegerField('高度', default=150)
    color = models.CharField('背景色', max_length=50, default='rgba(52, 152, 219, 0.08)')
    border_color = models.CharField('边框色', max_length=50, default='rgba(52, 152, 219, 0.3)')
    sort_order = models.IntegerField('排序', default=0)

    class Meta:
        verbose_name = '区域'
        verbose_name_plural = '区域配置'
        ordering = ['sort_order']

    def __str__(self):
        return self.name