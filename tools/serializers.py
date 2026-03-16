# E:\repair_shop_tool_system\tools\serializers.py

from rest_framework import serializers
from .models import Team, ToolCategory, Tool, ToolLoanRecord, MaintenanceRecord, \
    MaintenanceImage, RepairRecord


# --- 简化示例，可根据实际API接口需求调整 ---
class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'


class ToolCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolCategory
        fields = '__all__'


class ToolListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Tool
        fields = ['id', 'code', 'name', 'specification', 'category_name', 'status']


class ToolDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    custody_location_name = serializers.CharField(source='custody_location', read_only=True)  # 简化，实际可能关联Team
    tech_archive = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tool
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class ToolLoanRecordSerializer(serializers.ModelSerializer):
    tool_code = serializers.CharField(source='tool.code', read_only=True)
    borrower_name = serializers.CharField(source='borrower.get_full_name', read_only=True)
    team_leader_name = serializers.CharField(source='team_leader_approval.get_full_name', read_only=True)

    class Meta:
        model = ToolLoanRecord
        fields = '__all__'
        read_only_fields = ('loan_time', 'actual_return_time', 'status')


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    tool_code = serializers.CharField(source='tool.code', read_only=True)
    maintainer_name = serializers.CharField(source='maintainer.get_full_name', read_only=True)
    images = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = MaintenanceRecord
        fields = '__all__'
        read_only_fields = ('date',)


class RepairRecordSerializer(serializers.ModelSerializer):
    tool_code = serializers.CharField(source='tool.code', read_only=True)
    reporter_name = serializers.CharField(source='reporter.get_full_name', read_only=True)

    class Meta:
        model = RepairRecord
        fields = '__all__'
        read_only_fields = ('report_time',)