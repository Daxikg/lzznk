from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from app01.models import Admin  # 添加正确的导入


class Team(models.Model):
    """班组表"""
    name = models.CharField(max_length=100, unique=True, verbose_name="班组名称")
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leading_teams',
                               verbose_name="负责人")

    # 权限控制字段
    can_borrow_tools = models.BooleanField(default=True, verbose_name="可申领工具")
    can_manage_custody = models.BooleanField(default=False, verbose_name="可管理保管")
    can_perform_maintenance = models.BooleanField(default=False, verbose_name="可执行保养")
    can_approve_loans = models.BooleanField(default=False, verbose_name="可审批申领")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "班组"
        verbose_name_plural = "班组"


class ToolCategory(models.Model):
    """工具分类表"""
    name = models.CharField(max_length=100, verbose_name="分类名称")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "工具分类"
        verbose_name_plural = "工具分类"


class Tool(models.Model):
    """工具信息表"""
    STATUS_CHOICES = [
        ('正常', '正常'),
        ('故障', '故障'),
        ('维修', '维修'),
        ('报废', '报废'),
    ]

    MAINTENANCE_CYCLE_CHOICES = [
        (1, '每天'),
        (7, '一周'),
        (30, '一个月'),
        (60, '两个月'),
        (90, '三个月'),
        (180, '半年'),
        (365, '一年'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name="工具编码")
    name = models.CharField(max_length=200, verbose_name="名称")
    specification = models.CharField(max_length=200, verbose_name="规格")
    manufacturer = models.CharField(max_length=200, blank=True, null=True, verbose_name="厂家名称")
    category = models.ForeignKey(ToolCategory, on_delete=models.CASCADE, verbose_name="类别")
    purchase_date = models.DateField(verbose_name="购买日期")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="价值(元)")
    HIGH_VALUE_CHOICES = [
        (False, '普通工具'),
        (True, '高价值工具'),
    ]
    is_high_value = models.BooleanField(default=False, choices=HIGH_VALUE_CHOICES, verbose_name="工具类型",
                                       help_text="价值≥1000元的工具建议选择高价值工具")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='正常', verbose_name="状态")
    maintenance_cycle = models.IntegerField(choices=MAINTENANCE_CYCLE_CHOICES, default=30,
                                          verbose_name="保养周期(天)", help_text="工具保养的时间间隔")
    last_maintenance_date = models.DateField(null=True, blank=True, verbose_name="上次保养日期")
    image = models.ImageField(upload_to='tool_images/', blank=True, null=True, verbose_name="图片")
    technical_docs = models.FileField(upload_to='tech_docs/', blank=True, null=True, verbose_name="技术文档")
    remark = models.CharField(max_length=200, blank=True, null=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # 自动判断是否为高价值工具（价值>=1000元）
        if self.value and self.value >= 1000:
            self.is_high_value = True
        else:
            self.is_high_value = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def next_maintenance_date(self):
        """计算下次保养日期"""
        if not self.last_maintenance_date:
            return None
        from django.utils import timezone
        return self.last_maintenance_date + timezone.timedelta(days=self.maintenance_cycle)

    @property
    def days_until_next_maintenance(self):
        """计算距离下次保养的天数"""
        if not self.next_maintenance_date:
            return None
        from django.utils import timezone
        today = timezone.now().date()
        delta = self.next_maintenance_date - today
        return delta.days

    @property
    def is_due_for_maintenance(self):
        """判断是否到了保养时间"""
        days_left = self.days_until_next_maintenance
        if days_left is None:
            return False
        return days_left <= 0

    @property
    def maintenance_status_color(self):
        """获取保养状态对应的颜色类"""
        days_left = self.days_until_next_maintenance
        if days_left is None:
            return 'secondary'
        elif days_left <= 0:
            return 'danger'  # 已过期
        elif days_left <= 3:
            return 'warning'  # 即将到期
        elif days_left <= 7:
            return 'info'     # 一周内到期
        else:
            return 'success'  # 正常

    class Meta:
        verbose_name = "工具"
        verbose_name_plural = "工具"


class ToolLoanRecord(models.Model):
    """申领记录表"""
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, verbose_name="工具")
    borrower = models.ForeignKey('app01.Admin', on_delete=models.CASCADE, verbose_name="申领人")
    team_leader_approval = models.ForeignKey('app01.Admin', on_delete=models.SET_NULL, null=True, related_name='approved_loans',
                                             verbose_name="班组长审批")
    return_approval = models.ForeignKey('app01.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='return_approved_loans',
                                       verbose_name="归还审批人")
    # 新增字段：申领班组和申领人
    borrowing_team = models.CharField(max_length=50, verbose_name="申领班组", help_text="申领工具的班组名称")
    borrowing_person = models.CharField(max_length=50, verbose_name="申领人", help_text="实际使用工具的人员姓名")
    borrowing_person_id = models.IntegerField(null=True, blank=True, verbose_name="申领人ID",
                                            help_text="申领人对应的TeamUser ID，用于关联查询")
    loan_time = models.DateTimeField(auto_now_add=True, verbose_name="申领时间")
    expected_return_time = models.DateTimeField(null=True, blank=True, verbose_name="预计归还时间")
    actual_return_time = models.DateTimeField(null=True, blank=True, verbose_name="实际归还时间")
    status = models.CharField(max_length=20, choices=[('已申请', '已申请'), ('已发放', '已发放'), ('归还申请', '归还申请'), ('已归还', '已归还'),
                                                      ('逾期', '逾期')], default='已申请')
    remarks = models.TextField(blank=True, verbose_name="备注")

    def __str__(self):
        return f"{self.tool.code} - {self.borrower.username} - {self.loan_time}"

    @property
    def is_overdue(self):
        """判断是否逾期"""
        if self.status == '已发放' and self.expected_return_time:
            from django.utils import timezone
            return timezone.now() > self.expected_return_time
        return False

    class Meta:
        verbose_name = "工具申领记录"
        verbose_name_plural = "工具申领记录"


class MaintenanceRecord(models.Model):
    """保养记录表"""
    MAINTENANCE_TYPE_CHOICES = [
        ('日常', '日常'),
        ('定期', '定期'),
        ('校准', '校准'),
    ]

    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, verbose_name="工具")
    maintainer = models.ForeignKey('app01.Admin', on_delete=models.CASCADE, verbose_name="保养人")
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES, verbose_name="保养类型")
    date = models.DateField(default=timezone.now, verbose_name="日期")
    content = models.TextField(verbose_name="保养内容")
    result = models.TextField(verbose_name="保养结果")
    images = models.ManyToManyField('MaintenanceImage', blank=True, verbose_name="相关图片")

    def __str__(self):
        return f"{self.tool.code} - {self.maintenance_type} - {self.date}"

    class Meta:
        verbose_name = "保养记录"
        verbose_name_plural = "保养记录"


class MaintenanceImage(models.Model):
    """保养记录中的图片"""
    image = models.ImageField(upload_to='maintenance_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.uploaded_at}"


class ScrapRecord(models.Model):
    """报废记录表"""
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, verbose_name="工具")
    scrap_person = models.ForeignKey('app01.Admin', on_delete=models.CASCADE, verbose_name="报废人")
    scrap_reason = models.TextField(verbose_name="报废原因")
    scrap_time = models.DateTimeField(auto_now_add=True, verbose_name="报废时间")
    images = models.ManyToManyField('ScrapImage', blank=True, verbose_name="相关附件")

    def __str__(self):
        return f"{self.tool.code} - 报废 - {self.scrap_time.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "报废记录"
        verbose_name_plural = "报废记录"


class ScrapImage(models.Model):
    """报废记录中的附件（图片或PDF）"""
    file = models.FileField(upload_to='scrap_files/', verbose_name="附件文件",
                           help_text="支持图片或PDF文件")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    def __str__(self):
        return f"附件 - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"


class RepairRecord(models.Model):
    """维修记录表"""
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, verbose_name="工具")
    # 报修人关联到 Admin 模型
    reporter = models.ForeignKey('app01.Admin', on_delete=models.CASCADE, verbose_name="报修人")
    fault_description = models.TextField(verbose_name="故障描述")
    report_time = models.DateTimeField(auto_now_add=True, verbose_name="报修时间")
    repair_status = models.CharField(max_length=20,
                                     choices=[('待维修', '待维修'), ('已完成', '已完成')],
                                     default='待维修', verbose_name="维修状态")
    repair_unit = models.CharField(max_length=100, blank=True, verbose_name="维修单位")
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="费用 (元)")
    resolution_notes = models.TextField(blank=True, verbose_name="维修说明")
    liability_identified = models.BooleanField(default=False, verbose_name="是否已认定责任")
    liability_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                           verbose_name="赔偿金额 (元)")

    def __str__(self):
        return f"{self.tool.code} - {self.repair_status}"

    class Meta:
        verbose_name = "维修记录"
        verbose_name_plural = "维修记录"


class Profile(models.Model):
    """用户扩展信息"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="用户")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="所属班组")
    position = models.CharField(max_length=20, choices=[
        ('班组长', '班组长'),
        ('操作员', '操作员'),
        ('信息管理员', '信息管理员'),
        ('车间主任', '车间主任')
    ], default='操作员', verbose_name="职务")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.position}"

    class Meta:
        verbose_name = "用户档案"
        verbose_name_plural = "用户档案"


# 创建用户时自动创建Profile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.create(user=instance)


class SimpleTeamPermission(models.Model):
    """简化的班组权限配置 - 只包含必需的权限"""
    workshop = models.IntegerField(choices=Admin.chejian_choices, verbose_name="车间")
    team = models.IntegerField(choices=Admin.banzu_choices, verbose_name="班组")

    # 必需的七大权限
    can_manage_tools = models.BooleanField(default=False, verbose_name="工具管理权限")
    can_manage_categories = models.BooleanField(default=False, verbose_name="分类管理权限")
    can_approve_loans = models.BooleanField(default=False, verbose_name="申领审批权限")
    can_approve_returns = models.BooleanField(default=False, verbose_name="归还审批权限")
    can_perform_maintenance = models.BooleanField(default=False, verbose_name="执行保养权限")
    can_manage_repairs = models.BooleanField(default=False, verbose_name="维修管理权限")
    can_view_records = models.BooleanField(default=False, verbose_name="查看记录权限")

    # 班组长信息
    team_leader_username = models.CharField(max_length=32, blank=True,
                                          verbose_name="班组长用户名")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "班组权限配置"
        verbose_name_plural = "班组权限配置"
        unique_together = ['workshop', 'team']

    def __str__(self):
        workshop_dict = dict(Admin.chejian_choices)
        team_dict = dict(Admin.banzu_choices)
        workshop_name = workshop_dict.get(self.workshop, f'车间{self.workshop}')
        team_name = team_dict.get(self.team, f'班组{self.team}')
        return f"{workshop_name}-{team_name} 权限配置"