# E:\repair_shop_tool_system\tools\urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # 用于登录登出
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect

app_name = 'tools'  # 添加应用命名空间

# 自定义logout视图，支持GET请求
def custom_logout(request):
    if request.method == 'POST' or request.method == 'GET':
        # 执行登出操作
        from django.contrib.auth import logout
        logout(request)
        # 重定向到登录页面
        return redirect('login')
    # 如果是其他方法，使用默认的LogoutView
    return LogoutView.as_view()(request)

urlpatterns = [
    # path('', views.index, name='index'), # 如果有首页视图的话
    path('login_tools/', views.login_tools, name='login_tools'),
    path('logout/', views.tools_register, name='logout'),  # 使用自定义的logout视图
    path('dashboard/', views.user_dashboard, name='user_dashboard'),


    path('api/team-permission/<int:workshop>/<int:team>/', views.get_team_permission_api, name='get_team_permission_api'),
    path('api/position-permission/<str:position>/', views.get_position_permission_api, name='get_position_permission_api'),
    path('api/tool-category/<int:category_id>/', views.get_tool_category_api, name='get_tool_category_api'),
    path('api/team-users/<int:team_id>/', views.get_team_users_api, name='get_team_users_api'),
    path('api/tool-detail/<int:tool_id>/', views.get_tool_detail_api, name='get_tool_detail_api'),
    path('permissions/user/', views.manage_user_permissions, name='manage_user_permissions'),
    path('permissions/simple/', views.simple_permissions, name='simple_permissions'),
    path('permissions/position/<str:position>/', views.edit_position_permissions, name='edit_position_permissions'),
    path('categories/create/', views.create_tool_category, name='create_tool_category'),
    path('categories/<int:category_id>/update/', views.update_tool_category, name='update_tool_category'),
    path('categories/<int:category_id>/delete/', views.delete_tool_category, name='delete_tool_category'),
    path('categories/manage/', views.manage_tool_categories, name='manage_tool_categories'),
    path('tools/create/', views.create_tool, name='create_tool'),
    path('tools/<int:tool_id>/update/', views.update_tool, name='update_tool'),
    path('tools/<int:tool_id>/delete/', views.delete_tool, name='delete_tool'),
    path('tools/<int:tool_id>/scrap/', views.scrap_tool, name='scrap_tool'),
    path('tools/manage/', views.manage_tools, name='manage_tools'),

    path('tools/<int:tool_id>/loan-history/', views.tool_loan_history, name='tool_loan_history'),  # 工具申领历史
    path('tools/<int:tool_id>/loan/', views.loan_tool, name='loan_tool'),
    path('loans/<int:loan_id>/approve/', views.approve_loan, name='approve_loan'),
    path('loans/<int:loan_id>/return-approve/', views.approve_return, name='approve_return'),
    path('loans/<int:loan_id>/return/', views.return_tool, name='return_tool'),
    path('api/approve-loan/<int:loan_id>/', views.ajax_approve_loan, name='ajax_approve_loan'),
    path('tools/<int:tool_id>/maintenance/create/', views.create_maintenance_record, name='create_maintenance_record'),
    path('tools/<int:tool_id>/report-fault/', views.report_fault, name='report_fault'),
    path('tools/<int:tool_id>/repair-records/', views.tool_repair_records, name='tool_repair_records'),
    path('tools/<int:tool_id>/maintenance-records/', views.tool_maintenance_records, name='tool_maintenance_records'),
    path('repair-records/<int:record_id>/update/', views.update_repair_record, name='update_repair_record'),
    path('repair-records/manage/', views.manage_repair_records, name='manage_repair_records'),
    path('index/', views.index, name='index'),

    # 自由下载区功能 - 注意：具体路由必须放在<path>路由之前
    path('1/upload/', views.upload_files_free, name='upload_files_free'),
    path('1/create-folder/', views.create_folder_free, name='create_folder_free'),
    path('1/rename/', views.rename_item_free, name='rename_item_free'),
    path('1/delete/', views.delete_files_free, name='delete_files_free'),
    path('1/search/', views.search_files_free, name='search_files_free'),
    path('1/download/<path:rel_path>/', views.download_file_free, name='download_file_free'),
    path('1/preview/<path:rel_path>/', views.preview_file_free, name='preview_file_free'),
    path('1/', views.file_explorer_free, name='file_explorer_free_root'),
    path('1/<path:rel_path>/', views.file_explorer_free, name='file_explorer_free'),
]
