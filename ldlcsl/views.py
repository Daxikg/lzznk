from django.db.models import Sum
from django.forms import ModelForm
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import TruncMonth
from app01.views import LoginForm, logger
from app01 import models
from .models import InventoryRecord, Inventory
from django.contrib import messages


class InventoryForm(ModelForm):
    class Meta:
        model = Inventory
        fields = ['old_axle_D_a', 'old_axle_E_a', 'old_wheel_D_a', 'old_wheel_E_a', 'new_axle_D_a', 'new_axle_E_a',
                  'new_wheel_D_a', 'new_wheel_E_a', 'old_axle_D_b', 'old_axle_E_b', 'old_wheel_D_b', 'old_wheel_E_b',
                  'new_axle_D_b', 'new_axle_E_b', 'new_wheel_D_b', 'new_wheel_E_b', 'old_axle_D_c', 'old_axle_E_c',
                  'old_wheel_D_c', 'old_wheel_E_c', 'new_axle_D_c', 'new_axle_E_c', 'new_wheel_D_c', 'new_wheel_E_c']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {'class': 'form-control'}


def Inventory_edit(request):
    initial = Inventory.objects.first()  # 获取初始库存记录
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=initial)
        if form.is_valid():
            form.save()
            return redirect('/ldlcsl/ldlcsl_index/')  # 保存后跳回首页
    else:
        form = InventoryForm(instance=initial)

    return render(request, 'Inventory_edit.html', {'form': form})


class InventoryRecordForm(ModelForm):
    class Meta:
        model = InventoryRecord
        fields = ['factory', 'operation_type', 'record_date', 'old_axle_D_a', 'old_axle_E_a', 'old_wheel_D_a',
                  'old_wheel_E_a', 'new_axle_D_a', 'new_axle_E_a', 'new_wheel_D_a', 'new_wheel_E_a']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {'class': 'form-control'}


def ldlcsl_index(request):
    initial = Inventory.objects.first()
    records = InventoryRecord.objects.all().order_by('record_date')
    sum_records = (records
                   .annotate(month=TruncMonth('record_date'))  # 提取年份和月份
                   .values('month')
                   .annotate(total_old_axle_D_a=Sum('old_axle_D_a') + initial.old_axle_D_a,
                             total_old_axle_E_a=Sum('old_axle_E_a') + initial.old_axle_E_a,
                             total_old_wheel_D_a=Sum('old_wheel_D_a') + initial.old_wheel_D_a,
                             total_old_wheel_E_a=Sum('old_wheel_E_a') + initial.old_wheel_E_a,
                             total_new_axle_D_a=Sum('new_axle_D_a') + initial.new_axle_D_a,
                             total_new_axle_E_a=Sum('new_axle_E_a') + initial.new_axle_E_a,
                             total_new_wheel_D_a=Sum('new_wheel_D_a') + initial.new_wheel_D_a,
                             total_new_wheel_E_a=Sum('new_wheel_E_a') + initial.new_wheel_E_a,
                             total_old_axle_D_b=Sum('old_axle_D_b') + initial.old_axle_D_b,
                             total_old_axle_E_b=Sum('old_axle_E_b') + initial.old_axle_E_b,
                             total_old_wheel_D_b=Sum('old_wheel_D_b') + initial.old_wheel_D_b,
                             total_old_wheel_E_b=Sum('old_wheel_E_b') + initial.old_wheel_E_b,
                             total_new_axle_D_b=Sum('new_axle_D_b') + initial.new_axle_D_b,
                             total_new_axle_E_b=Sum('new_axle_E_b') + initial.new_axle_E_b,
                             total_new_wheel_D_b=Sum('new_wheel_D_b') + initial.new_wheel_D_b,
                             total_new_wheel_E_b=Sum('new_wheel_E_b') + initial.new_wheel_E_b,
                             total_old_axle_D_c=Sum('old_axle_D_c') + initial.old_axle_D_c,
                             total_old_axle_E_c=Sum('old_axle_E_c') + initial.old_axle_E_c,
                             total_old_wheel_D_c=Sum('old_wheel_D_c') + initial.old_wheel_D_c,
                             total_old_wheel_E_c=Sum('old_wheel_E_c') + initial.old_wheel_E_c,
                             total_new_axle_D_c=Sum('new_axle_D_c') + initial.new_axle_D_c,
                             total_new_axle_E_c=Sum('new_axle_E_c') + initial.new_axle_E_c,
                             total_new_wheel_D_c=Sum('new_wheel_D_c') + initial.new_wheel_D_c,
                             total_new_wheel_E_c=Sum('new_wheel_E_c') + initial.new_wheel_E_c,
                             )
                   .order_by('month'))
    form = InventoryRecordForm()
    context = {
        'initial': initial,
        'records': records,
        'form': form,
        'sum_records': sum_records,
    }
    return render(request, "ldlcsl_index.html", context)


@csrf_exempt
def ldlcsl_add(request):
    if request.method == 'GET':
        form = InventoryRecordForm()
        return render(request, 'ldlcsl_index.html', {'form': form})
    else:
        form = InventoryRecordForm(request.POST)
        if form.is_valid():
            model_instance = form.save(commit=False)
            operation_type = model_instance.operation_type
            factory = model_instance.factory

            old_axle_D_a = model_instance.old_axle_D_a
            old_axle_E_a = model_instance.old_axle_E_a
            old_wheel_D_a = model_instance.old_wheel_D_a
            old_wheel_E_a = model_instance.old_wheel_E_a

            new_axle_D_a = model_instance.new_axle_D_a
            new_axle_E_a = model_instance.new_axle_E_a
            new_wheel_D_a = model_instance.new_wheel_D_a
            new_wheel_E_a = model_instance.new_wheel_E_a
            print(operation_type, factory, old_axle_D_a, old_axle_E_a, )
            if operation_type == '本段调出':
                if factory == '贵厂':
                    model_instance.old_axle_D_a = -old_axle_D_a
                    model_instance.old_axle_E_a = -old_axle_E_a
                    model_instance.old_wheel_D_a = -old_wheel_D_a
                    model_instance.old_wheel_E_a = -old_wheel_E_a

                    model_instance.new_axle_D_a = -new_axle_D_a
                    model_instance.new_axle_E_a = -new_axle_E_a
                    model_instance.new_wheel_D_a = -new_wheel_D_a
                    model_instance.new_wheel_E_a = -new_wheel_E_a

                    model_instance.old_axle_D_b = old_axle_D_a
                    model_instance.old_axle_E_b = old_axle_E_a
                    model_instance.old_wheel_D_b = old_wheel_D_a
                    model_instance.old_wheel_E_b = old_wheel_E_a

                    model_instance.new_axle_D_b = new_axle_D_a
                    model_instance.new_axle_E_b = new_axle_E_a
                    model_instance.new_wheel_D_b = new_wheel_D_a
                    model_instance.new_wheel_E_b = new_wheel_E_a

                    model_instance.old_axle_D_c = 0
                    model_instance.old_axle_E_c = 0
                    model_instance.old_wheel_D_c = 0
                    model_instance.old_wheel_E_c = 0

                    model_instance.new_axle_D_c = 0
                    model_instance.new_axle_E_c = 0
                    model_instance.new_wheel_D_c = 0
                    model_instance.new_wheel_E_c = 0

                    model_instance.save()
                    messages.success(request, f'新记录添加成功！')
                elif factory == '成都北':
                    model_instance.old_axle_D_a = -old_axle_D_a
                    model_instance.old_axle_E_a = -old_axle_E_a
                    model_instance.old_wheel_D_a = -old_wheel_D_a
                    model_instance.old_wheel_E_a = -old_wheel_E_a

                    model_instance.new_axle_D_a = -new_axle_D_a
                    model_instance.new_axle_E_a = -new_axle_E_a
                    model_instance.new_wheel_D_a = -new_wheel_D_a
                    model_instance.new_wheel_E_a = -new_wheel_E_a

                    model_instance.old_axle_D_b = 0
                    model_instance.old_axle_E_b = 0
                    model_instance.old_wheel_D_b = 0
                    model_instance.old_wheel_E_b = 0

                    model_instance.new_axle_D_b = 0
                    model_instance.new_axle_E_b = 0
                    model_instance.new_wheel_D_b = 0
                    model_instance.new_wheel_E_b = 0

                    model_instance.old_axle_D_c = old_axle_D_a
                    model_instance.old_axle_E_c = old_axle_E_a
                    model_instance.old_wheel_D_c = old_wheel_D_a
                    model_instance.old_wheel_E_c = old_wheel_E_a

                    model_instance.new_axle_D_c = 0
                    model_instance.new_axle_E_c = 0
                    model_instance.new_wheel_D_c = 0
                    model_instance.new_wheel_E_c = 0

                    model_instance.save()
                    messages.success(request, f'新记录添加成功！')
            elif operation_type == '调入本段':
                if factory == '贵厂':
                    model_instance.old_axle_D_a = old_axle_D_a
                    model_instance.old_axle_E_a = old_axle_E_a
                    model_instance.old_wheel_D_a = old_wheel_D_a
                    model_instance.old_wheel_E_a = old_wheel_E_a

                    model_instance.new_axle_D_a = new_axle_D_a
                    model_instance.new_axle_E_a = new_axle_E_a
                    model_instance.new_wheel_D_a = new_wheel_D_a
                    model_instance.new_wheel_E_a = new_wheel_E_a

                    model_instance.old_axle_D_b = -old_axle_D_a
                    model_instance.old_axle_E_b = -old_axle_E_a
                    model_instance.old_wheel_D_b = -old_wheel_D_a
                    model_instance.old_wheel_E_b = -old_wheel_E_a

                    model_instance.new_axle_D_b = -new_axle_D_a
                    model_instance.new_axle_E_b = -new_axle_E_a
                    model_instance.new_wheel_D_b = -new_wheel_D_a
                    model_instance.new_wheel_E_b = -new_wheel_E_a

                    model_instance.old_axle_D_c = 0
                    model_instance.old_axle_E_c = 0
                    model_instance.old_wheel_D_c = 0
                    model_instance.old_wheel_E_c = 0

                    model_instance.new_axle_D_c = 0
                    model_instance.new_axle_E_c = 0
                    model_instance.new_wheel_D_c = 0
                    model_instance.new_wheel_E_c = 0

                    model_instance.save()
                    messages.success(request, f'新记录添加成功！')
                elif factory == '成都北':
                    model_instance.old_axle_D_a = old_axle_D_a
                    model_instance.old_axle_E_a = old_axle_E_a
                    model_instance.old_wheel_D_a = old_wheel_D_a
                    model_instance.old_wheel_E_a = old_wheel_E_a

                    model_instance.new_axle_D_a = new_axle_D_a
                    model_instance.new_axle_E_a = new_axle_E_a
                    model_instance.new_wheel_D_a = new_wheel_D_a
                    model_instance.new_wheel_E_a = new_wheel_E_a

                    model_instance.old_axle_D_b = 0
                    model_instance.old_axle_E_b = 0
                    model_instance.old_wheel_D_b = 0
                    model_instance.old_wheel_E_b = 0

                    model_instance.new_axle_D_b = 0
                    model_instance.new_axle_E_b = 0
                    model_instance.new_wheel_D_b = 0
                    model_instance.new_wheel_E_b = 0

                    model_instance.old_axle_D_c = -old_axle_D_a
                    model_instance.old_axle_E_c = -old_axle_E_a
                    model_instance.old_wheel_D_c = -old_wheel_D_a
                    model_instance.old_wheel_E_c = -old_wheel_E_a

                    model_instance.new_axle_D_c = 0
                    model_instance.new_axle_E_c = 0
                    model_instance.new_wheel_D_c = 0
                    model_instance.new_wheel_E_c = 0

                    model_instance.save()
                    messages.success(request, f'新记录添加成功！')
            elif operation_type == '检修新品消耗':
                model_instance.old_axle_D_a = new_axle_D_a
                model_instance.old_axle_E_a = new_axle_E_a
                model_instance.old_wheel_D_a = new_wheel_D_a
                model_instance.old_wheel_E_a = new_wheel_E_a

                model_instance.new_axle_D_a = -new_axle_D_a
                model_instance.new_axle_E_a = -new_axle_E_a
                model_instance.new_wheel_D_a = -new_wheel_D_a
                model_instance.new_wheel_E_a = -new_wheel_E_a

                model_instance.save()
                messages.success(request, f'新记录添加成功！')
            elif operation_type == '报废':
                if factory == '贵厂':
                    model_instance.old_axle_D_a = 0
                    model_instance.old_axle_E_a = 0
                    model_instance.old_wheel_D_a = 0
                    model_instance.old_wheel_E_a = 0

                    model_instance.new_axle_D_a = 0
                    model_instance.new_axle_E_a = 0
                    model_instance.new_wheel_D_a = 0
                    model_instance.new_wheel_E_a = 0

                    model_instance.old_axle_D_b = -old_axle_D_a
                    model_instance.old_axle_E_b = -old_axle_E_a
                    model_instance.old_wheel_D_b = -old_wheel_D_a
                    model_instance.old_wheel_E_b = -old_wheel_E_a

                    model_instance.new_axle_D_b = -new_axle_D_a
                    model_instance.new_axle_E_b = -new_axle_E_a
                    model_instance.new_wheel_D_b = -new_wheel_D_a
                    model_instance.new_wheel_E_b = -new_wheel_E_a

                    model_instance.save()
                    messages.success(request, f'新记录添加成功！')
                elif factory == '成都北':

                    model_instance.old_axle_D_a = 0
                    model_instance.old_axle_E_a = 0
                    model_instance.old_wheel_D_a = 0
                    model_instance.old_wheel_E_a = 0

                    model_instance.new_axle_D_a = 0
                    model_instance.new_axle_E_a = 0
                    model_instance.new_wheel_D_a = 0
                    model_instance.new_wheel_E_a = 0

                    model_instance.old_axle_D_c = -old_axle_D_a
                    model_instance.old_axle_E_c = -old_axle_E_a
                    model_instance.old_wheel_D_c = -old_wheel_D_a
                    model_instance.old_wheel_E_c = -old_wheel_E_a

                    model_instance.new_axle_D_c = -new_axle_D_a
                    model_instance.new_axle_E_c = -new_axle_E_a
                    model_instance.new_wheel_D_c = -new_wheel_D_a
                    model_instance.new_wheel_E_c = -new_wheel_E_a

                    model_instance.save()
                    messages.success(request, f'新记录添加成功！')
            # 如果没有错误发生，重定向到指定的url
            messages.warning(request, f'记录添加失败！')
            return HttpResponseRedirect(reverse('ldlcsl:ldlcsl_index'))
        else:
            # 如果表单无效（例如，因为提供的数据无效），则重新显示表单
            messages.warning(request, f'记录添加失败！')
            return render(request, 'ldlcsl_index.html', {'form': form})


@csrf_exempt
def ldlcsl_delete(request, id):
    instance = get_object_or_404(InventoryRecord, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.info(request, f'记录已被删除！')
        return JsonResponse({'status': 'ok'})
    return render(request, 'ldlcsl_index.html')
