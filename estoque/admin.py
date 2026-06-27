from django.contrib import admin
from .models import Estoque, MovimentoEstoque

@admin.register(Estoque)
class EstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'loja', 'quantidade', 'estoque_minimo', 'abaixo_minimo')
    list_filter = ('loja',)
    search_fields = ('produto__nome',)

@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('estoque', 'tipo', 'quantidade', 'criado_em')
    list_filter = ('tipo', 'criado_em')
