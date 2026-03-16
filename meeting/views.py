from itertools import groupby
from operator import attrgetter

from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from .models import meeting
from django.views import View
from django.forms import ModelForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


class MeetingForm(ModelForm):
    class Meta:
        model = meeting
        fields = ['meeting', 'meeting1', 'Contents', 'Contents1', 'Contents2', 'Contents3',
                  'Contents4', 'Contents5', 'Contents6', 'Contents7']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in ['meeting', 'meeting1', 'Contents']:
                field.widget = forms.Textarea(attrs={'rows': 1, 'class': 'form-control'})
            elif name in ["Contents1", "Contents2", "Contents3", "Contents4", 'Contents5', "Contents6", "Contents7"]:
                field.widget = forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
            elif field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs = {'class': 'form-control'}


def meeting0(request, id=None):
    if id is None:
        last_meeting = meeting.objects.last()
        if last_meeting:
            id = last_meeting.id
        else:
            id = None
    else:
        last_meeting = meeting.objects.get(id=id)
    form = MeetingForm(instance=last_meeting)  # 绑定实例数据
    return render(request, "meeting0.html", {'meeting': last_meeting, 'id': id, 'form': form})


def meeting1(request, id=None):
    if id is None:
        last_meeting = meeting.objects.last()
        if last_meeting:
            id = last_meeting.id
        else:
            id = None
    else:
        last_meeting = meeting.objects.get(id=id)
    form = MeetingForm(instance=last_meeting)  # 绑定实例数据
    return render(request, "meeting1.html", {'meeting': last_meeting, 'id': id, 'form': form})


def meeting2(request, id=None):
    if id is None:
        last_meeting = meeting.objects.last()
        if last_meeting:
            id = last_meeting.id
        else:
            id = None
    else:
        last_meeting = meeting.objects.get(id=id)
    form = MeetingForm(instance=last_meeting)  # 绑定实例数据
    return render(request, "meeting2.html", {'meeting': last_meeting, 'id': id, 'form': form})


def meeting3(request, id=None):
    if id is None:
        last_meeting = meeting.objects.last()
        if last_meeting:
            id = last_meeting.id
        else:
            id = None
    else:
        last_meeting = meeting.objects.get(id=id)
    form = MeetingForm(instance=last_meeting)  # 绑定实例数据
    return render(request, "meeting3.html", {'meeting': last_meeting, 'id': id, 'form': form})


class AddMeetingView(View):
    def get(self, request):
        form = MeetingForm()
        return render(request, 'add_meeting.html', {'form': form})

    def post(self, request):
        form = MeetingForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect('/meeting/meeting1')


@csrf_exempt
def edit_meeting(request):
    if request.method == 'POST':
        log_id = request.POST.get('logid')  # 注意参数名称匹配
        log = get_object_or_404(meeting, id=log_id)
        form = MeetingForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': '保存成功!'})
        return JsonResponse({'error': form.errors}, status=400)
    return JsonResponse({'error': '无效请求'}, status=400)


def history_meetings(request):
    meetings = meeting.objects.order_by('-time')  # 按时间降序排列
    context = {
        'meetings': meetings,
    }
    return render(request, "history_meetings.html", context)


@csrf_exempt
def delete_meeting(request, id):
    instance = get_object_or_404(meeting, id=id)
    if request.method == 'POST':
        instance.delete()
        return JsonResponse({'status': 'ok'})
    return render(request, 'history_meetings.html')

