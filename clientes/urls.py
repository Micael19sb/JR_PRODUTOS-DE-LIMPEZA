from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista, name='cliente_lista'),
    path('novo/', views.novo, name='cliente_novo'),
    path('novo-ajax/', views.novo_ajax, name='cliente_novo_ajax'),
    path('<int:pk>/', views.detalhe, name='cliente_detalhe'),
    path('<int:pk>/editar/', views.editar, name='cliente_editar'),
    path('<int:pk>/excluir/', views.excluir, name='cliente_excluir'),
    path('<int:pk>/quitar-tudo/', views.quitar_tudo, name='cliente_quitar_tudo'),
]
