from django.urls import path
from . import views
from .views import AddMeetingView

app_name = 'meeting'

urlpatterns = [
    path('meeting0/', views.meeting0, name='meeting0'),
    path('meeting1/<int:id>/', views.meeting1, name='meeting1'),
    path('meeting1/', views.meeting1, name='meeting1_default'),
    path('meeting2/<int:id>/', views.meeting2, name='meeting2'),
    path('meeting2/', views.meeting2, name='meeting2_default'),
    path('meeting3/<int:id>/', views.meeting3, name='meeting3'),
    path('meeting3/', views.meeting3, name='meeting3_default'),
    path('create', AddMeetingView.as_view(), name='add_meeting'),
    path('edit_meeting/', views.edit_meeting, name='edit_meeting'),
    path('history_meetings/', views.history_meetings, name='history_meetings'),
    path('delete/<int:id>/', views.delete_meeting, name='delete_meeting'),

]
