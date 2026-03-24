from django.db import models
import os


def qrcode_upload_path(instance, filename):
    """二维码图片上传路径：E:/credential/workshop/设备编号.扩展名"""
    ext = filename.split('.')[-1] if '.' in filename else 'png'
    return f'workshop/{instance.device_id}.{ext}'


class DeviceType(models.Model):
    """设备类型"""
    code = models.CharField('类型代码', max_length=30, unique=True, help_text='如: detect, lathe')
    name = models.CharField('类型名称', max_length=50, help_text='如: 检测设备')
    sort_order = models.IntegerField('排序', default=0)

    class Meta:
        verbose_name = '设备类型'
        verbose_name_plural = '设备类型'
        ordering = ['sort_order', 'code']

    def __str__(self):
        return self.name


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


class Device(models.Model):
    """设备模型"""
    STATUS_CHOICES = [
        ('running', '运行中'),
        ('fault', '故障'),
        ('offline', '离线'),
    ]

    device_id = models.CharField('设备编号', max_length=20, unique=True)
    name = models.CharField('设备名称', max_length=100)
    area = models.ForeignKey(DeviceArea, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属区域')
    device_type = models.ForeignKey(DeviceType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='设备类型')
    description = models.CharField('设备描述', max_length=200, blank=True, default='')

    # 状态相关
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='offline')
    fault_time = models.DateTimeField('故障发生时间', null=True, blank=True)

    # 位置信息（用于大屏展示）
    pos_x = models.IntegerField('X坐标', default=0)
    pos_y = models.IntegerField('Y坐标', default=0)
    pos_width = models.IntegerField('宽度', default=100)
    pos_height = models.IntegerField('高度', default=60)

    # 二维码图片
    qrcode_image = models.ImageField('设备二维码', upload_to=qrcode_upload_path, blank=True, null=True)

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
            if fault_duration.total_seconds() > 2 * 60 * 60:
                return 'longFault'
        return self.status