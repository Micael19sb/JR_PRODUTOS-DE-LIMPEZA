from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista, name='estoque_lista'),
    path('<int:pk>/entrada/', views.entrada, name='estoque_entrada'),
    path('<int:pk>/ajuste/', views.ajuste, name='estoque_ajuste'),
    path('<int:pk>/historico/', views.historico, name='estoque_historico'),
]
