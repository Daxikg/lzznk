from django.urls import path
from . import views


app_name = 'ldlcsl'

urlpatterns = [
    path('ldlcsl_index/', views.ldlcsl_index, name='ldlcsl_index'),
    path('ldlcsl_add/', views.ldlcsl_add, name='ldlcsl_add'),
    path('Inventory_edit/', views.Inventory_edit, name='Inventory_edit'),
    path('ldlcsl_delete/<int:id>/', views.ldlcsl_delete, name='ldlcsl_delete'),
]