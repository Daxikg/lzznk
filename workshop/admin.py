from django.contrib import admin
from .models import Device, DeviceArea, DeviceType


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'sort_order']
    list_editable = ['name', 'sort_order']
    ordering = ['sort_order', 'code']
    search_fields = ['code', 'name']


@admin.register(DeviceArea)
class DeviceAreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'pos_x', 'pos_y', 'width', 'height', 'sort_order']
    list_editable = ['pos_x', 'pos_y', 'width', 'height', 'sort_order']
    ordering = ['sort_order']


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'name', 'area', 'device_type', 'status', 'pos_x', 'pos_y', 'pos_width', 'pos_height', 'has_qrcode', 'updated_at']
    list_filter = ['status', 'area', 'device_type']
    search_fields = ['device_id', 'name']
    list_editable = ['name', 'area', 'device_type', 'status']
    ordering = ['device_id']

    # 编辑页面字段配置
    fieldsets = (
        ('基本信息', {
            'fields': ('device_id', 'name', 'device_type', 'area', 'description')
        }),
        ('位置信息', {
            'fields': ('pos_x', 'pos_y', 'pos_width', 'pos_height')
        }),
        ('状态信息', {
            'fields': ('status', 'fault_time')
        }),
        ('设备二维码', {
            'fields': ('qrcode_image',)
        }),
        ('立体库信息', {
            'fields': ('capacity', 'used'),
            'classes': ('collapse',),
            'description': '仅立体库和堆垛系统需要填写'
        }),
    )

    def has_qrcode(self, obj):
        return '是' if obj.qrcode_image else '否'
    has_qrcode.short_description = '二维码'