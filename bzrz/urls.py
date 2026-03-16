from django.urls import path
from bzrz import views

app_name = 'bzrz'

urlpatterns = [
    path('login2/', views.login2, name='login2'),
    path('register2/', views.register2),
    path('teamlog0/', views.teamlog0, name='teamlog0'),
    path('teamlog1/<int:banzu>/', views.teamlog1, name='teamlog1'),
    path('license/<str:banzu>/<int:id>/', views.license, name='license'),
    path('license1/<str:banzu>/<int:id>/', views.license1, name='license2'),
    path('license2/<str:banzu>/<int:id>/', views.license2, name='license2'),
    path('teamlog/delete/<int:log_id>', views.delete_teamlog, ),
    path('teamlog/<int:banzu>/<int:year>/<int:log_id>/', views.teamlog, name='teamlog'),
    path('add_teamuser/<int:banzu>/', views.add_teamuser, name='add_teamuser'),
    path('edit_teamuser/', views.edit_teamuser, name='edit_teamuser'),
    path('create_teamlog/<int:banzu>/', views.create_teamlog, name='create_teamlog'),
    path('edit_teamlog/', views.edit_teamlog, name='edit_teamlog'),
]
