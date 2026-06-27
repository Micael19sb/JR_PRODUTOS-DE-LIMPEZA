from django.contrib import admin
from .models import MovimentoCaixa, ContaReceber, Despesa, FechamentoCaixa


@admin.register(MovimentoCaixa)
class MovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = ['data', 'tipo', 'categoria', 'descricao', 'valor']
    list_filter = ['tipo', 'categoria']


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'valor_total', 'valor_pago', 'vencimento', 'status']
    list_filter = ['status']


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'categoria', 'valor', 'data', 'pago']
    list_filter = ['categoria', 'pago']


@admin.register(FechamentoCaixa)
class FechamentoCaixaAdmin(admin.ModelAdmin):
    list_display = ['data', 'total_entradas', 'total_despesas', 'saldo_fechamento', 'fechado']
