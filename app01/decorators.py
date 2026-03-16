from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from .models import Admin

def check_user_role(required_roles):
    """
    检查用户角色的装饰器
    兼容原有的角色检查逻辑
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # 检查用户是否已认证
            if not request.user.is_authenticated:
                return redirect('/login/')
            
            # 获取用户的角色信息
            try:
                if hasattr(request.user, 'admin'):
                    user_role = request.user.admin.role
                else:
                    admin_user = Admin.objects.get(username=request.user.username)
                    user_role = admin_user.role
            except Admin.DoesNotExist:
                return HttpResponseForbidden("用户不存在")
            
            # 检查角色权限
            if user_role in required_roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("权限不足")
        
        return _wrapped_view
    return decorator

# 保持原有的装饰器名称以确保向后兼容
allowed_users = check_user_role