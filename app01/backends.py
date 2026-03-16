from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import Admin

class AdminAuthBackend(BaseBackend):
    """
    自定义认证后端，支持现有的Admin模型
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            admin_user = Admin.objects.get(username=username)
            # 检查密码（支持原有的MD5和新的Django哈希）
            if admin_user.check_password(password):
                return admin_user
        except Admin.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            return Admin.objects.get(pk=user_id)
        except Admin.DoesNotExist:
            return None