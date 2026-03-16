from django.contrib import admin
from .models import Device, DeviceArea


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'name', 'area', 'device_type', 'status', 'updated_at']
    list_filter = ['status', 'area', 'device_type']
    search_fields = ['device_id', 'name']
    list_editable = ['status']
    ordering = ['device_id']


@admin.register(DeviceArea)
class DeviceAreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'pos_x', 'pos_y', 'width', 'height', 'sort_order']
    list_editable = ['pos_x', 'pos_y', 'width', 'height', 'sort_order']
    ordering = ['sort_order']