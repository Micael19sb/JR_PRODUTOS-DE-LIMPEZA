from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista, name='produto_lista'),
    path('novo/', views.novo, name='produto_novo'),
    path('novo-ajax/', views.novo_ajax, name='produto_novo_ajax'),
    path('categoria-ajax/', views.categoria_ajax, name='categoria_ajax'),
    path('<int:pk>/editar/', views.editar, name='produto_editar'),
    path('<int:pk>/editar-ajax/', views.editar_ajax, name='produto_editar_ajax'),
    path('<int:pk>/excluir/', views.excluir, name='produto_excluir'),
]
