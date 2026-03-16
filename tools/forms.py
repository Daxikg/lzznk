# E:\repair_shop_tool_system\tools\forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Team, ToolCategory, Tool, ToolLoanRecord, MaintenanceRecord, RepairRecord, MaintenanceImage


# 自定义一个支持多文件上传的Widget
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(file, initial) for file in data]
        else:
            result = single_file_clean(data, initial)
        return result


class CreateUserForm(UserCreationForm):
    team = forms.ModelChoiceField(queryset=Team.objects.all(), required=False, label="所属班组")
    position = forms.ChoiceField(choices=[('班组长', '班组长'), ('操作员', '操作员'), ('信息管理员', '信息管理员'), ('车间主任', '车间主任')], 
                                required=True, label="职务")

    class Meta:
        model = User
        fields = ("username", "team", "position", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 移除必填字段的星号标记
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        # 如果没有班组，显示提示信息
        if not Team.objects.exists():
            self.fields['team'].help_text = "暂无班组，请先创建班组"

    def save(self, commit=True):
        user = super().save(commit=False)
        team = self.cleaned_data.get('team')
        position = self.cleaned_data.get('position')
        
        if commit:
            user.save()
            # 创建或更新Profile
            profile, created = user.profile, hasattr(user, 'profile')
            if not created:
                profile = user.profile
            profile.team = team
            profile.position = position
            profile.save()
            
            # 根据选择的职务分配Group
            position_group_mapping = {
                '班组长': 'Foremen',
                '操作员': 'Operators',
                '信息管理员': 'InfoAdmins',
                '车间主任': 'WorkshopDirectors'
            }
            
            group_name = position_group_mapping.get(position, 'Operators')
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

        return user


class UpdateUserForm(forms.ModelForm):
    team = forms.ModelChoiceField(queryset=Team.objects.all(), required=False, label="所属班组")
    position = forms.ChoiceField(choices=[('班组长', '班组长'), ('操作员', '操作员'), ('信息管理员', '信息管理员'), ('车间主任', '车间主任')], 
                                required=False, label="职务")
    # 管理员权限选项
    is_info_admin = forms.BooleanField(required=False, label="信息管理员权限")
    is_workshop_director = forms.BooleanField(required=False, label="车间主任权限")
    is_foreman = forms.BooleanField(required=False, label="班组长权限")
    is_operator = forms.BooleanField(required=False, label="操作员权限")

    class Meta:
        model = User
        fields = ("username", "team", "position")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果用户已有Profile，初始化表单字段
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['team'].initial = self.instance.profile.team
            self.fields['position'].initial = self.instance.profile.position
        
        # 初始化权限字段
        if self.instance:
            user_groups = self.instance.groups.values_list('name', flat=True)
            self.fields['is_info_admin'].initial = 'InfoAdmins' in user_groups
            self.fields['is_workshop_director'].initial = 'WorkshopDirectors' in user_groups
            self.fields['is_foreman'].initial = 'Foremen' in user_groups
            self.fields['is_operator'].initial = 'Operators' in user_groups

    def save(self, commit=True):
        user = super().save(commit=False)
        team = self.cleaned_data.get('team')
        position = self.cleaned_data.get('position')
        
        if commit:
            user.save()
            # 更新Profile
            if hasattr(user, 'profile'):
                profile = user.profile
            else:
                from .models import Profile
                profile = Profile.objects.create(user=user)
            
            profile.team = team
            profile.position = position
            profile.save()
            
            # 更新权限组
            user.groups.clear()
            if self.cleaned_data.get('is_info_admin'):
                group, created = Group.objects.get_or_create(name='InfoAdmins')
                user.groups.add(group)
            if self.cleaned_data.get('is_workshop_director'):
                group, created = Group.objects.get_or_create(name='WorkshopDirectors')
                user.groups.add(group)
            if self.cleaned_data.get('is_foreman'):
                group, created = Group.objects.get_or_create(name='Foremen')
                user.groups.add(group)
            if self.cleaned_data.get('is_operator'):
                group, created = Group.objects.get_or_create(name='Operators')
                user.groups.add(group)
        
        return user


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'leader', 'can_borrow_tools', 'can_manage_custody', 
                  'can_perform_maintenance', 'can_approve_loans']
        # 已经移除了 storage_location 和 priority_level 字段


class ToolCategoryForm(forms.ModelForm):
    class Meta:
        model = ToolCategory
        fields = ['name']


class CreateToolForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置购买日期默认为今天
        if not self.initial.get('purchase_date'):
            today = timezone.now().date()
            self.fields['purchase_date'].initial = today
            # 同时设置widget的attrs
            self.fields['purchase_date'].widget.attrs['value'] = today.strftime('%Y-%m-%d')
        
        # 设置工具类型的帮助文本
        self.fields['is_high_value'].help_text = "可根据价值自动判断或手动选择"
        
        # 设置上次保养日期默认为今天
        if not self.initial.get('last_maintenance_date'):
            today = timezone.now().date()
            self.fields['last_maintenance_date'].initial = today
            self.fields['last_maintenance_date'].widget.attrs['value'] = today.strftime('%Y-%m-%d')
    
    class Meta:
        model = Tool
        fields = ['code', 'name', 'specification', 'manufacturer', 'remark', 'category', 'purchase_date', 'value',
                  'is_high_value', 'status', 'maintenance_cycle', 'last_maintenance_date', 
                  'image', 'technical_docs']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'value': forms.NumberInput(attrs={'step': '0.01', 'id': 'tool_value'}),
            'is_high_value': forms.Select(attrs={'id': 'tool_type'}),
            'maintenance_cycle': forms.Select(),
            'last_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
        }


class UpdateToolForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置购买日期默认为今天（如果未设置）
        if not self.initial.get('purchase_date') and not self.instance.pk:
            today = timezone.now().date()
            self.fields['purchase_date'].initial = today
            # 同时设置 widget 的 attrs
            self.fields['purchase_date'].widget.attrs['value'] = today.strftime('%Y-%m-%d')
            
        # 设置工具类型的帮助文本
        self.fields['is_high_value'].help_text = "可根据价值自动判断或手动选择"
            
        # 禁用状态字段，防止通过编辑页面修改状态
        self.fields['status'].widget.attrs['disabled'] = 'disabled'
        self.fields['status'].required = False
        
        # 设置上次保养日期：编辑时显示现有值，新建时默认为今天
        if self.instance.pk:
            # 编辑现有工具
            if hasattr(self.instance, 'last_maintenance_date') and self.instance.last_maintenance_date:
                # 如果已有上次保养日期，使用现有值
                formatted_date = self.instance.last_maintenance_date.strftime('%Y-%m-%d')
                self.fields['last_maintenance_date'].initial = self.instance.last_maintenance_date
                self.fields['last_maintenance_date'].widget.attrs['value'] = formatted_date
                # 确保widget的format属性正确设置
                self.fields['last_maintenance_date'].widget.format = '%Y-%m-%d'
            else:
                # 如果没有上次保养日期，使用今天作为默认值
                today = timezone.now().date()
                formatted_today = today.strftime('%Y-%m-%d')
                self.fields['last_maintenance_date'].initial = today
                self.fields['last_maintenance_date'].widget.attrs['value'] = formatted_today
                self.fields['last_maintenance_date'].widget.format = '%Y-%m-%d'
        else:
            # 新建工具时，默认为今天
            today = timezone.now().date()
            formatted_today = today.strftime('%Y-%m-%d')
            self.fields['last_maintenance_date'].initial = today
            self.fields['last_maintenance_date'].widget.attrs['value'] = formatted_today
            self.fields['last_maintenance_date'].widget.format = '%Y-%m-%d'
    
    class Meta:
        model = Tool
        fields = ['code', 'name', 'specification', 'manufacturer', 'remark', 'category', 'purchase_date', 'value',
                  'is_high_value', 'status', 'maintenance_cycle', 'last_maintenance_date', 
                  'image', 'technical_docs']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'value': forms.NumberInput(attrs={'step': '0.01', 'id': 'tool_value'}),
            'is_high_value': forms.Select(attrs={'id': 'tool_type'}),
            'maintenance_cycle': forms.Select(),
            'last_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
        }


class LoanRequestForm(forms.ModelForm):
    # 添加申领时间字段
    loan_datetime = forms.DateTimeField(
        label='申领时间',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False,
        help_text='默认为当前时间，可修改'
    )
    
    # 显式定义borrowing_person_id字段
    borrowing_person_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    def __init__(self, *args, **kwargs):
        # 获取当前用户信息
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # 设置申领时间默认为现在
        if not self.initial.get('loan_datetime'):
            now = timezone.now()
            self.fields['loan_datetime'].initial = now
            # 同时设置widget的value属性
            self.fields['loan_datetime'].widget.attrs['value'] = now.strftime('%Y-%m-%dT%H:%M')
        
        # 设置预计归还时间默认为明天此时
        if not self.initial.get('expected_return_time'):
            tomorrow = timezone.now() + timezone.timedelta(days=1)
            self.fields['expected_return_time'].initial = tomorrow
            # 同时设置widget的value属性
            self.fields['expected_return_time'].widget.attrs['value'] = tomorrow.strftime('%Y-%m-%dT%H:%M')
        
        # 如果有当前用户信息，设置默认申领班组
        if self.current_user and hasattr(self.current_user, 'banzu'):
            from app01.models import Admin
            banzu_dict = dict(Admin.banzu_choices)
            default_team = banzu_dict.get(self.current_user.banzu, '')
            self.fields['borrowing_team'].initial = default_team
            
        # 添加班组选择的选项
        from app01.models import Admin
        team_choices = [('', '---------')] + list(Admin.banzu_choices)
        self.fields['borrowing_team'].widget = forms.Select(choices=team_choices)
        
        # 申领人字段设置为下拉选择
        self.fields['borrowing_person'].widget = forms.Select(choices=[('', '---------')])
        

        
    class Meta:
        model = ToolLoanRecord
        fields = ['borrowing_team', 'borrowing_person', 'borrowing_person_id', 'loan_datetime', 'expected_return_time', 'remarks']
        widgets = {
            'expected_return_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'borrowing_team': forms.Select(),
            'borrowing_person': forms.Select(),
        }
        
    def clean_borrowing_person(self):
        """验证申领人信息"""
        borrowing_person = self.cleaned_data.get('borrowing_person')
        borrowing_person_id = self.cleaned_data.get('borrowing_person_id')
        
        # 如果从cleaned_data获取不到，尝试从原始数据获取
        if not borrowing_person_id and 'borrowing_person_id' in self.data:
            borrowing_person_id = self.data.get('borrowing_person_id')
            # 如果是字符串，尝试转换为整数
            if isinstance(borrowing_person_id, str) and borrowing_person_id.isdigit():
                borrowing_person_id = int(borrowing_person_id)
        
        if borrowing_person and not borrowing_person_id:
            raise forms.ValidationError("请选择有效的申领人")
        
        return borrowing_person


class ReturnToolForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置实际归还时间默认为现在
        now = timezone.now()
        self.fields['actual_return_time'].initial = now
        self.fields['actual_return_time'].widget.attrs['value'] = now.strftime('%Y-%m-%dT%H:%M')
        self.fields['actual_return_time'].widget.attrs['class'] = 'form-control'
        self.fields['remarks'].widget.attrs['class'] = 'form-control'
        self.fields['remarks'].widget.attrs['rows'] = '2'
        self.fields['remarks'].widget.attrs['placeholder'] = '可选，填写归还备注'

    class Meta:
        model = ToolLoanRecord
        fields = ['actual_return_time', 'remarks']
        widgets = {
            'actual_return_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class MaintenanceRecordForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 设置保养日期默认为今天
        if not self.initial.get('date'):
            self.fields['date'].initial = timezone.now().date()
    
    images = MultipleFileField(required=False)  # 添加多文件字段

    class Meta:
        model = MaintenanceRecord
        fields = ['maintenance_type', 'date', 'content', 'result', 'images']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            # 移除 'images' 的 widget，因为我们要用自定义的 MultipleFileField
            # 'images': forms.ClearableFileInput(attrs={'multiple': True}), # 删除这行
        }


class RepairRecordForm(forms.ModelForm):
    class Meta:
        model = RepairRecord
        fields = ['repair_status', 'fault_description', 'repair_unit', 'cost', 'resolution_notes', 'liability_identified',
                  'liability_amount']
        widgets = {
            'cost': forms.NumberInput(attrs={'step': '0.01'}),
            'liability_amount': forms.NumberInput(attrs={'step': '0.01'}),
        }


class FaultReportForm(forms.Form):
    """故障报修表单 - 包含班组和人员选择"""
    
    # 班组选择
    team = forms.ChoiceField(
        label='报修班组',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    # 人员选择
    reporter_name = forms.CharField(
        label='报修人',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        help_text='请先选择班组，然后选择报修人'
    )
    
    # 人员ID（隐藏字段）
    reporter_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    # 故障描述
    fault_description = forms.CharField(
        label='故障描述',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '请输入详细的故障描述...',
            'required': True
        }),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        # 提前获取 initial 数据
        initial_data = kwargs.get('initial', {})
        
        super().__init__(*args, **kwargs)
        
        # 设置班组选择选项
        from bzrz.models import TeamUser
        team_choices = [('', '请选择报修班组')] + list(TeamUser.banzu_choices)
        self.fields['team'].choices = team_choices
        
        # 如果有初始数据，设置默认班组
        if initial_data and 'team' in initial_data:
            self.fields['team'].initial = initial_data['team']