from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista, name='estoque_lista'),
    path('<int:pk>/entrada/', views.entrada, name='estoque_entrada'),
    path('<int:pk>/ajuste/', views.ajuste, name='estoque_ajuste'),
    path('<int:pk>/historico/', views.historico, name='estoque_historico'),
    path('<int:pk>/entrada-ajax/', views.entrada_ajax, name='estoque_entrada_ajax'),
    path('<int:pk>/ajuste-ajax/', views.ajuste_ajax, name='estoque_ajuste_ajax'),
    path('<int:pk>/historico-ajax/', views.historico_ajax, name='estoque_historico_ajax'),
]
