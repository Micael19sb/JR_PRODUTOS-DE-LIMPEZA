from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'loja', 'telefone', 'ativo')
    list_filter = ('loja', 'ativo')
    search_fields = ('nome', 'telefone', 'cpf_cnpj')
