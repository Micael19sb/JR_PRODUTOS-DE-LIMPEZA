from django.contrib import admin
from .models import Produto, Categoria

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'categoria', 'unidade', 'preco_venda', 'ativo')
    list_filter = ('categoria', 'ativo', 'unidade')
    search_fields = ('nome', 'codigo')
    list_editable = ('preco_venda', 'ativo')
