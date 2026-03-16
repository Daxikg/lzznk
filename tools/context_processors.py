from app01.models import Admin
from .models import SimpleTeamPermission


def tools_context_processor(request):
    """
    Tools应用的上下文处理器
    确保所有页面都能获得用户权限信息
    只使用班组权限配置（SimpleTeamPermission）
    """
    context = {}

    # 只对已登录用户处理
    if not request.user.is_authenticated:
        return context

    try:
        # 获取对应的Admin用户对象
        admin_user = Admin.objects.get(username=request.user.username)

        # 获取班组权限配置
        try:
            team_perm = SimpleTeamPermission.objects.get(
                workshop=admin_user.chejian,
                team=admin_user.banzu
            )

            # 使用班组权限配置
            context.update({
                'can_manage_tools': team_perm.can_manage_tools,
                'can_manage_categories': team_perm.can_manage_categories,
                'can_approve_loans': team_perm.can_approve_loans,
                'can_approve_returns': team_perm.can_approve_returns,
                'can_perform_maintenance': team_perm.can_perform_maintenance,
                'can_manage_repairs': team_perm.can_manage_repairs,
                'can_view_reports': team_perm.can_view_records,
                'can_manage_permissions': admin_user.username == 'admin',
                'is_admin': (team_perm.can_manage_tools or
                           team_perm.can_manage_categories or
                           team_perm.can_perform_maintenance or
                           team_perm.can_manage_repairs),
            })

        except SimpleTeamPermission.DoesNotExist:
            # 没有班组权限配置，使用默认权限（无任何权限）
            context.update({
                'can_manage_tools': False,
                'can_manage_categories': False,
                'can_approve_loans': False,
                'can_approve_returns': False,
                'can_perform_maintenance': False,
                'can_manage_repairs': False,
                'can_view_reports': False,
                'can_manage_permissions': admin_user.username == 'admin',
                'is_admin': False,
            })

    except Admin.DoesNotExist:
        # 用户不存在时的默认权限
        context.update({
            'can_manage_tools': False,
            'can_manage_categories': False,
            'can_approve_loans': False,
            'can_approve_returns': False,
            'can_perform_maintenance': False,
            'can_manage_repairs': False,
            'can_view_reports': False,
            'can_manage_permissions': False,
            'is_admin': False,
        })

    return context