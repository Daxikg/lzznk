# tools/utils.py
from django.utils import timezone
from .models import SimpleTeamPermission, Admin

def check_user_permission(admin_user, permission_name):
    """检查用户是否具有指定权限"""
    # 检查班组权限
    try:
        team_config = SimpleTeamPermission.objects.get(
            workshop=admin_user.chejian,
            team=admin_user.banzu
        )
        return getattr(team_config, f'can_{permission_name}', False)
    except SimpleTeamPermission.DoesNotExist:
        return False

def get_user_permissions(admin_user):
    """获取用户所有权限"""
    permissions = {}
    permission_list = [
        'manage_tools', 'manage_categories', 'approve_loans',
        'approve_returns', 'perform_maintenance', 'manage_repairs', 'view_records'
    ]

    for perm in permission_list:
        permissions[perm] = check_user_permission(admin_user, perm)

    return permissions

def is_team_leader(admin_user):
    """检查是否为班组长"""
    try:
        team_config = SimpleTeamPermission.objects.get(
            workshop=admin_user.chejian,
            team=admin_user.banzu
        )
        return team_config.team_leader_username == admin_user.username
    except SimpleTeamPermission.DoesNotExist:
        return False

def get_team_members(workshop, team):
    """获取指定班组的所有成员"""
    return Admin.objects.filter(chejian=workshop, banzu=team)

def get_user_team_info(admin_user):
    """获取用户所在班组信息"""
    workshop_dict = dict(Admin.chejian_choices)
    team_dict = dict(Admin.banzu_choices)

    return {
        'workshop_id': admin_user.chejian,
        'workshop_name': workshop_dict.get(admin_user.chejian, ''),
        'team_id': admin_user.banzu,
        'team_name': team_dict.get(admin_user.banzu, ''),
        'is_team_leader': is_team_leader(admin_user)
    }

# 便捷的权限检查函数
def can_manage_tools(admin_user):
    return check_user_permission(admin_user, 'manage_tools')

def can_manage_categories(admin_user):
    return check_user_permission(admin_user, 'manage_categories')

def can_approve_loans(admin_user):
    return check_user_permission(admin_user, 'approve_loans')

def can_approve_returns(admin_user):
    return check_user_permission(admin_user, 'approve_returns')

def can_perform_maintenance(admin_user):
    return check_user_permission(admin_user, 'perform_maintenance')

def can_manage_repairs(admin_user):
    return check_user_permission(admin_user, 'manage_repairs')

def can_view_records(admin_user):
    return check_user_permission(admin_user, 'view_records')