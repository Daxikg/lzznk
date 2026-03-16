from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    自定义权限只允许管理员写入，其他用户只读。
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS: # GET, HEAD, OPTIONS
            return True
        return request.user and request.user.is_staff

class IsTeamMemberOrAdmin(permissions.BasePermission):
    """
    允许工具所属班组成员或管理员操作。
    此处简化示例，实际逻辑可能需要更复杂的判断（例如高价值工具的申领权限）
    """
    def has_object_permission(self, request, view, obj):
        # 示例：如果是Tool对象，且用户属于该工具所在班组（通过custody_location或其他字段关联）
        # 或者是超级用户
        if hasattr(obj, 'team') and request.user in obj.team.users.all():
            return True
        return request.user.is_staff