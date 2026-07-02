from django.urls import path
from . import views
urlpatterns = [
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('relatorio/', views.relatorio_mensal, name='relatorio_mensal'),
]
