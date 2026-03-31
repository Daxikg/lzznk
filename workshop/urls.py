from django.urls import path, re_path
from django.views.static import serve
from django.conf import settings
from . import views

app_name = 'workshop'

urlpatterns = [
    # 页面
    path('', views.workshop_screen, name='screen'),

    # 静态文件（开发环境）
    re_path(r'^static/(?P<path>.*)$', serve, {
        'document_root': r'E:\lzznk\workshop\static',
    }),

    # API接口
    path('api/devices/', views.get_devices, name='api_devices'),
    path('api/devices/<str:device_id>/', views.get_device_detail, name='api_device_detail'),
    path('api/devices/<str:device_id>/status/', views.update_device_status, name='api_update_status'),
    path('api/devices/<str:device_id>/repairs/', views.get_repair_records, name='api_device_repairs'),
    path('api/statistics/', views.get_statistics, name='api_statistics'),
    path('api/areas/', views.get_areas, name='api_areas'),
    path('api/all/', views.get_all_data, name='api_all'),
    path('api/sync/', views.sync_data, name='api_sync'),
    path('api/repairs/', views.get_repair_records, name='api_repairs'),
    path('api/scheduler/status/', views.get_scheduler_status_api, name='api_scheduler_status'),
    path('api/scheduler/control/', views.control_scheduler, name='api_scheduler_control'),
]