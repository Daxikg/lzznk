from django.contrib import admin
from .models import Device, DeviceArea, DeviceType, InspectionRecord, RepairRecord, SyncConfig


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
    list_display = ['device_id', 'name', 'area', 'device_type', 'status', 'auto_status', 'pos_x', 'pos_y', 'pos_width', 'pos_height', 'has_qrcode', 'updated_at']
    list_filter = ['status', 'auto_status', 'area', 'device_type']
    search_fields = ['device_id', 'name']
    list_editable = ['name', 'area', 'device_type', 'status', 'auto_status']
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
            'fields': ('status', 'fault_time', 'inspection_start', 'inspection_end', 'inspection_location')
        }),
        ('设备二维码', {
            'fields': ('qrcode_image',)
        }),
    )

    readonly_fields = ['inspection_start', 'inspection_end', 'inspection_location']

    def has_qrcode(self, obj):
        return '是' if obj.qrcode_image else '否'
    has_qrcode.short_description = '二维码'


@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'device_name', 'location', 'start_time', 'end_time', 'sync_time']
    list_filter = ['start_time', 'end_time']
    search_fields = ['device_id', 'device_name']
    ordering = ['-start_time']
    readonly_fields = ['sync_time']


@admin.register(RepairRecord)
class RepairRecordAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'device_name', 'location', 'fault_date', 'reporter', 'repair_date', 'worker', 'is_resolved', 'sync_time']
    list_filter = ['is_resolved', 'department', 'repair_team', 'fault_date', 'repair_date']
    search_fields = ['device_id', 'device_name', 'reporter', 'worker', 'phenomenon']
    ordering = ['-fault_date']
    readonly_fields = ['sync_time', 'external_id']
    list_display_links = ['device_id', 'device_name']


@admin.register(SyncConfig)
class SyncConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'api_url', 'is_enabled', 'sync_interval', 'last_sync', 'last_status']
    list_editable = ['is_enabled', 'sync_interval']
    readonly_fields = ['last_sync', 'last_status', 'last_error']