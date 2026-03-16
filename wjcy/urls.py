from django.urls import path
from . import views

app_name = 'wjcy'

urlpatterns = [
    path('wjcy/', views.wjcy, name='wjcy'),
    path('wjcy_detail/<int:circulate_id>/', views.circulate_detail, name='circulate_detail'),
    path('mark_as_read/', views.mark_as_read, name='mark_as_read'),
    path('upload_photo/', views.upload_photo, name='upload_photo'),
    path('save_beizhu/', views.save_beizhu, name='save_beizhu'),
    path('add_circulate/', views.add_circulate, name='add_circulate'),
    path('get_team_users/', views.get_team_users, name='get_team_users'),
    path('get_user_info/<int:user_id>/', views.get_user_info, name='get_user_info'),
    path('end_circulate/<int:circulate_id>/', views.end_circulate, name='end_circulate'),
    path('delete/<int:circulate_id>/', views.wjcy_delete, name='wjcy_delete'),
    path('history/', views.history, name='history'),

]
