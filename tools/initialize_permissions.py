"""
Tools应用班组权限初始化脚本
为现有的车间班组创建SimpleTeamPermission权限配置
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from app01.models import Admin
from tools.models import SimpleTeamPermission


def initialize_team_permissions():
    """初始化班组权限配置"""
    print("开始初始化班组权限配置...")

    # 获取所有唯一的车间-班组组合
    workshop_team_combinations = Admin.objects.values('chejian', 'banzu').distinct()

    created_count = 0
    updated_count = 0

    workshop_dict = dict(Admin.chejian_choices)
    team_dict = dict(Admin.banzu_choices)

    for combo in workshop_team_combinations:
        workshop = combo['chejian']
        team = combo['banzu']
        workshop_name = workshop_dict.get(workshop, f'车间{workshop}')
        team_name = team_dict.get(team, f'班组{team}')

        # 获取或创建班组权限配置
        perm, created = SimpleTeamPermission.objects.get_or_create(
            workshop=workshop,
            team=team,
            defaults={
                'can_manage_tools': False,
                'can_manage_categories': False,
                'can_approve_loans': False,
                'can_approve_returns': False,
                'can_perform_maintenance': False,
                'can_manage_repairs': False,
                'can_view_records': False,
            }
        )

        if created:
            print(f"✓ 为 {workshop_name}-{team_name} 创建了权限配置")
            created_count += 1
        else:
            print(f"- {workshop_name}-{team_name} 已有权限配置")
            updated_count += 1

    print(f"\n初始化完成!")
    print(f"创建配置: {created_count} 个")
    print(f"已存在配置: {updated_count} 个")


if __name__ == '__main__':
    initialize_team_permissions()