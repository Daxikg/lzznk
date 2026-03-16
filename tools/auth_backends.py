from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from app01.models import Admin


class ToolsAuthBackend(BaseBackend):
    """
    Tools应用专用认证后端
    基于现有的Admin用户，权限由SimpleTeamPermission班组权限控制
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # 使用现有的Admin用户进行基础认证
            admin_user = Admin.objects.get(username=username)
            if admin_user.check_password(password):
                # 检查是否具有tools应用访问权限
                if self._check_tools_access(admin_user):
                    return admin_user
        except Admin.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            admin_user = Admin.objects.get(pk=user_id)
            # 所有Admin用户都可以访问（权限由SimpleTeamPermission控制）
            return admin_user
        except Admin.DoesNotExist:
            return None

    def _check_tools_access(self, admin_user):
        """
        检查用户是否具有访问tools应用的权限
        根据角色和车间班组进行判断
        """
        # 允许访问的角色：信息班、修配管理员、车间主任等
        allowed_roles = ['role12', 'role18', 'role19', 'role1', 'role7', 'role8', 'role9']
        # 允许的车间：修配车间
        allowed_chejian = [1]  # 修配车间

        return (admin_user.role in allowed_roles or
                admin_user.chejian in allowed_chejian)