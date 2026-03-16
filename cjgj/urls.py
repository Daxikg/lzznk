from django.urls import path
from . import views

app_name = 'cjgj'

urlpatterns = [
    path('cjgj_login/', views.cjgj_login, name='cjgj_login'),
    path('cjgj_register/', views.cjgj_register, name='cjgj_register'),
    path('cjgj/', views.cjgj, name='cjgj'),
    path('zzgljg/', views.zzgljg, name='zzgljg'),
    path('cjglzd/', views.cjglzd, name='cjglzd'),
    path('upload_rule/', views.upload_rule, name='upload_rule'),
]
