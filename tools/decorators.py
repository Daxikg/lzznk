from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseForbidden

def tools_login_required(view_func):
    """
    Tools应用专用登录验证装饰器
    确保用户已登录且具有tools应用访问权限
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 检查用户是否已登录
        if not request.user.is_authenticated:
            messages.error(request, "请先登录系统")
            return redirect('login')
        
        # 检查是否具有tools应用访问权限
        if not hasattr(request.user, 'toolsuserprofile') or not request.user.toolsuserprofile.can_access_tools:
            messages.error(request, "您没有访问工具管理系统的权限")
            return redirect('index')  # 重定向到主系统首页
            
        return view_func(request, *args, **kwargs)
    return wrapper

def tools_permission_required(permission_name):
    """
    Tools应用专用权限检查装饰器
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 先检查登录状态
            if not request.user.is_authenticated:
                messages.error(request, "请先登录系统")
                return redirect('login')
            
            # 检查tools访问权限
            if not hasattr(request.user, 'toolsuserprofile') or not request.user.toolsuserprofile.can_access_tools:
                messages.error(request, "您没有访问工具管理系统的权限")
                return redirect('index')
            
            # 检查具体权限
            profile = request.user.toolsuserprofile
            if not profile.has_permission(permission_name):
                messages.error(request, f"您没有执行此操作的权限: {permission_name}")
                return redirect('tools:user_dashboard')
                
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def tools_role_required(*roles):
    """
    Tools应用角色权限装饰器
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 先检查登录状态
            if not request.user.is_authenticated:
                messages.error(request, "请先登录系统")
                return redirect('login')
            
            # 检查tools访问权限
            if not hasattr(request.user, 'toolsuserprofile') or not request.user.toolsuserprofile.can_access_tools:
                messages.error(request, "您没有访问工具管理系统的权限")
                return redirect('index')
            
            # 检查角色权限
            profile = request.user.toolsuserprofile
            if profile.tools_role not in roles:
                messages.error(request, f"此功能需要以下角色之一: {', '.join(roles)}")
                return redirect('tools:user_dashboard')
                
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def tools_admin_required(view_func):
    """
    Tools应用管理员权限装饰器
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 先检查登录状态
        if not request.user.is_authenticated:
            messages.error(request, "请先登录系统")
            return redirect('login')
        
        # 检查tools访问权限
        if not hasattr(request.user, 'toolsuserprofile') or not request.user.toolsuserprofile.can_access_tools:
            messages.error(request, "您没有访问工具管理系统的权限")
            return redirect('index')
        
        # 检查管理员权限
        profile = request.user.toolsuserprofile
        if not profile.is_admin_role():
            messages.error(request, "此功能需要管理员权限")
            return redirect('tools:user_dashboard')
            
        return view_func(request, *args, **kwargs)
    return wrapper

# 便捷的权限装饰器别名
tools_manage_users = tools_permission_required('manage_users')
tools_manage_teams = tools_permission_required('manage_teams')
tools_manage_tools = tools_permission_required('manage_tools')
tools_manage_categories = tools_permission_required('manage_categories')
tools_approve_loans = tools_permission_required('approve_loans')
tools_perform_maintenance = tools_permission_required('perform_maintenance')
tools_manage_repairs = tools_permission_required('manage_repairs')
tools_view_reports = tools_permission_required('view_reports')
tools_manage_permissions = tools_permission_required('manage_permissions')