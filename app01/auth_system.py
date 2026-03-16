"""
统一认证系统模块
提供跨app的认证和权限管理功能
"""

from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
from django.contrib import messages
from datetime import datetime
from .models import Admin
import logging

logger = logging.getLogger(__name__)

# 角色到页面的映射
ROLE_REDIRECT_MAP = {
    'role1': "/index/",           # 总管理员
    'role19': "/index/",          # 修配管理员
    'role20': "/index/",          # 修车管理员
    'role2': "/架车班信息采集界面1/",   # 架车班
    'role3': "/轮轴班信息采集界面1/",   # 轮轴班
    'role4': "/台车班顺序编辑1/",     # 台车班
    'role5': "/架车班信息手持机查看界面1/", # 架车班手持机
    'role6': "/index7/",          # 轮轴班手持机
    'role7': "/1/",               # 调度员
    'role8': "/1/",               # 安全员
    'role9': "/1/",               # 技术员
    'role10': "/1/",              # 内制动班
    'role11': "/1/",              # 外制动班
    'role12': "/1/",              # 车钩班
    'role13': "/1/",              # 探伤班
    'role14': "/1/",              # 调车组
    'role15': "/1/",              # 车体班
    'role16': "/1/",              # 预修班
    'role18': "/1/",              # 信息班
}

def unified_login(request, app_name="", template_name="login.html", success_redirect=None):
    """
    统一登录函数
    
    Args:
        request: HTTP请求对象
        app_name: 应用名称（用于日志记录）
        template_name: 登录模板名称
        success_redirect: 成功登录后的重定向URL（可选）
    
    Returns:
        登录页面或重定向响应
    """
    from .forms import LoginForm
    
    if request.method == "GET":
        form = LoginForm()
        return render(request, template_name, {"form": form})
    
    form = LoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        
        # 使用Django内置认证
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 登录用户
            auth_login(request, user)
            
            logger.info(f'{username} 在{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}登录了{app_name}。')
            
            # 设置session信息（为了兼容旧的检查逻辑）
            try:
                admin_user = Admin.objects.get(username=username)
                request.session["username"] = admin_user.username
                request.session["info"] = {
                    'id': admin_user.id,
                    'name': admin_user.username,
                    'role': admin_user.get_role_display(),
                    'role_code': admin_user.role,
                    'banzu': admin_user.banzu,
                    'chejian': admin_user.chejian,
                }
            except Admin.DoesNotExist:
                pass
            
            # 检查用户是否勾选了"保持登录状态"
            if "keep_logged_in" in request.POST:
                request.session.set_expiry(60 * 60 * 8)  # 8小时
            else:
                request.session.set_expiry(0)  # 浏览器关闭时过期
            
            # 根据用户角色重定向
            try:
                admin_user = Admin.objects.get(username=username)
                role = admin_user.role
                
                # 如果指定了成功重定向URL，则使用该URL
                if success_redirect:
                    redirect_url = success_redirect
                else:
                    # 否则使用角色映射
                    redirect_url = ROLE_REDIRECT_MAP.get(role, "/1/")
                
                return HttpResponseRedirect(redirect_url)
                
            except Admin.DoesNotExist:
                return HttpResponseRedirect("/1/")
        else:
            # 认证失败
            form.add_error(None, "账号或密码错误！")
            return render(request, template_name, {"form": form})
    
    return render(request, template_name, {"form": form})

def unified_logout(request, redirect_url="/login/"):
    """
    统一登出函数
    
    Args:
        request: HTTP请求对象
        redirect_url: 登出后的重定向URL
    
    Returns:
        重定向响应
    """
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    return redirect(redirect_url)

def check_user_permission(request, required_roles=None):
    """
    检查用户权限
    
    Args:
        request: HTTP请求对象
        required_roles: 需要的角色列表
    
    Returns:
        tuple: (是否有权限, 用户对象)
    """
    if not request.user.is_authenticated:
        return False, None
    
    try:
        admin_user = Admin.objects.get(username=request.user.username)
        if required_roles is None or admin_user.role in required_roles:
            return True, admin_user
        return False, admin_user
    except Admin.DoesNotExist:
        return False, None

def get_user_info(request):
    """
    获取当前用户信息
    
    Args:
        request: HTTP请求对象
    
    Returns:
        dict: 用户信息字典
    """
    if not request.user.is_authenticated:
        return None
    
    try:
        admin_user = Admin.objects.get(username=request.user.username)
        return {
            'id': admin_user.id,
            'username': admin_user.username,
            'name': admin_user.username,
            'role': admin_user.get_role_display(),
            'role_code': admin_user.role,
            'banzu': admin_user.banzu,
            'chejian': admin_user.chejian,
        }
    except Admin.DoesNotExist:
        return None