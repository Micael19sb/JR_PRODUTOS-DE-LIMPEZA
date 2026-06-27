from django.contrib import admin
from .models import Venda, ItemVenda

class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('pk', 'loja', 'cliente', 'forma_pagamento', 'status', 'criada_em')
    list_filter = ('loja', 'forma_pagamento', 'status', 'criada_em')
    inlines = [ItemVendaInline]
    readonly_fields = ('criada_em',)
