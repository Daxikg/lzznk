# E:\repair_shop_tool_system\tools\api_urls.py
# API专用URL配置

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'teams', views.TeamViewSet)
router.register(r'categories', views.ToolCategoryViewSet)

app_name = 'tools_api'  # API专用命名空间

urlpatterns = [
    path('', include(router.urls)),
    # 可以在这里添加额外的API端点
]