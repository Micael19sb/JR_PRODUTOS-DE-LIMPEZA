from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista, name='financeiro_lista'),
    path('baixa/<int:pk>/', views.dar_baixa, name='financeiro_baixa'),
    path('despesa/nova/', views.nova_despesa, name='financeiro_nova_despesa'),
    path('despesa/<int:pk>/excluir/', views.excluir_despesa, name='financeiro_excluir_despesa'),
]
