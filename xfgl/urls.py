from django.urls import path
from . import views

app_name = 'xfgl'

urlpatterns = [
    path('xfgl_login/', views.xfgl_login, name='xfgl_login'),
    path('register_xfgl/', views.register_xfgl, name='register_xfgl'),
    path('xfgl_index/', views.xfgl_index, name='xfgl_index'),
    path('xfgl/', views.xfgl, name='xfgl'),
    path('operater/', views.operater, name='operater'),
    path('add_operater/', views.add_operater, name='add_operater'),
    path('edit_operater/', views.edit_operater, name='edit_operater'),
    path('add_xfgl/', views.add_xfgl, name='add_xfgl'),
    path('edit_xfgl/', views.edit_xfgl, name='edit_xfgl'),
    path('info1/<int:id>', views.info1, name='info1'),
    path('info2/<int:id>', views.info2, name='info2'),
    path('info3/<int:id>', views.info3, name='info3'),
    path('sign1/<int:id>/', views.sign1, name='sign1'),
    path('sign2/<int:id>/', views.sign2, name='sign2'),
    path('sign3/<int:id>/', views.sign3, name='sign3'),
    path('check_complete/<int:id>/', views.check_complete, name='check_complete'),
    path('check_complete1/<int:id>/', views.check_complete1, name='check_complete1'),
    path('delete_check/<int:id>/', views.delete_check, name='delete_check'),
]
