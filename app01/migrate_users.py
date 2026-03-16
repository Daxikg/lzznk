#!/usr/bin/env python
"""
用户数据迁移脚本
将现有使用MD5加密的密码转换为Django的PBKDF2加密
"""

import os
import sys
import django

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from app01.models import Admin
from django.contrib.auth.hashers import make_password, is_password_usable
import hashlib
from django.conf import settings

def md5_hash(password):
    """原始的MD5加密方法"""
    obj = hashlib.md5(settings.SECRET_KEY.encode("utf-8"))
    obj.update(password.encode("utf-8"))
    return obj.hexdigest()

def migrate_user_passwords():
    """
    迁移所有用户的密码格式
    """
    print("开始迁移用户密码...")
    
    # 获取所有用户
    users = Admin.objects.all()
    migrated_count = 0
    
    for user in users:
        # 检查密码是否已经是Django格式
        if not is_password_usable(user.password):
            # 如果是原始MD5格式，则转换
            if len(user.password) == 32:  # MD5哈希长度
                # 由于我们无法反向MD5，这里我们假设有原始密码
                # 实际情况下，你可能需要让用户重置密码
                print(f"用户 {user.username} 使用MD5加密，需要重置密码")
                # 这里我们可以设置一个临时密码或者标记需要重置
                # 暂时跳过，让用户后续重置密码
                continue
            else:
                # 转换为Django标准格式
                user.password = make_password(user.password)
                user.save()
                migrated_count += 1
                print(f"已迁移用户: {user.username}")
    
    print(f"密码迁移完成！共迁移 {migrated_count} 个用户")
    return migrated_count

def create_superuser_if_not_exists():
    """
    如果没有超级用户，则创建一个
    """
    from django.contrib.auth.models import User
    
    if not User.objects.filter(is_superuser=True).exists():
        print("创建超级用户...")
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("超级用户 'admin' 已创建，密码: admin123")
    else:
        print("超级用户已存在")

def main():
    print("=== Django用户认证系统迁移工具 ===")
    
    try:
        # 迁移用户密码
        migrate_user_passwords()
        
        # 创建超级用户
        create_superuser_if_not_exists()
        
        print("\n迁移完成！")
        print("注意事项:")
        print("1. 原有的MD5密码用户需要重置密码")
        print("2. 建议通知所有用户尽快更改密码")
        print("3. 测试登录功能确保一切正常")
        
    except Exception as e:
        print(f"迁移过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()