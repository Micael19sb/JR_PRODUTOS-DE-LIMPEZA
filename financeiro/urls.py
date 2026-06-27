from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista, name='financeiro_lista'),
    path('fluxo/', views.fluxo_caixa, name='fluxo_caixa'),
    path('previsao/', views.previsao_caixa, name='previsao_caixa'),
    path('fechar-caixa/', views.fechar_caixa, name='fechar_caixa'),
    path('receber/<int:pk>/', views.receber_pagamento, name='receber_pagamento'),
    path('despesa/nova/', views.nova_despesa, name='financeiro_nova_despesa'),
    path('despesa/<int:pk>/excluir/', views.excluir_despesa, name='financeiro_excluir_despesa'),
    path('relatorio/enviar/', views.enviar_relatorio, name='enviar_relatorio'),
]
