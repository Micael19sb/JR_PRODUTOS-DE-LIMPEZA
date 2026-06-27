from django.urls import path
from . import views

urlpatterns = [
    path('pdv/', views.pdv, name='pdv'),
    path('buscar-produto/', views.buscar_produto, name='buscar_produto'),
    path('finalizar/', views.finalizar_venda, name='finalizar_venda'),
    path('', views.venda_lista, name='venda_lista'),
    path('<int:pk>/', views.venda_detalhe, name='venda_detalhe'),
    path('<int:pk>/cancelar/', views.cancelar_venda, name='venda_cancelar'),
]
