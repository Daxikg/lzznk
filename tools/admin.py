from django.contrib import admin
from .models import ScrapRecord, ScrapImage

# Register your models here.

@admin.register(ScrapRecord)
class ScrapRecordAdmin(admin.ModelAdmin):
    """报废记录管理"""
    list_display = ['tool', 'scrap_person', 'scrap_time', 'scrap_reason']
    list_filter = ['scrap_time', 'scrap_person']
    search_fields = ['tool__code', 'tool__name', 'scrap_reason']
    ordering = ['-scrap_time']
    filter_horizontal = ['images']  # 使用横向过滤器来显示多选的图片

@admin.register(ScrapImage)
class ScrapImageAdmin(admin.ModelAdmin):
    """报废附件管理"""
    list_display = ['file', 'uploaded_at']
    ordering = ['-uploaded_at']
