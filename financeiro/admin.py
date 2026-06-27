from django.contrib import admin
from .models import ContaReceber

@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'valor', 'vencimento', 'pago', 'vencida')
    list_filter = ('pago', 'vencimento')
    search_fields = ('cliente__nome',)
    list_editable = ('pago',)
