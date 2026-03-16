from django.urls import path
from . import views

app_name = 'workshop'

urlpatterns = [
    # API接口
    path('api/devices/', views.get_devices, name='api_devices'),
    path('api/devices/<str:device_id>/', views.get_device_detail, name='api_device_detail'),
    path('api/devices/<str:device_id>/status/', views.update_device_status, name='api_update_status'),
    path('api/statistics/', views.get_statistics, name='api_statistics'),
    path('api/areas/', views.get_areas, name='api_areas'),
    path('api/all/', views.get_all_data, name='api_all'),
]