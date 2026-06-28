from django.db import models
from lojas.models import Loja


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20, blank=True)
    cpf_cnpj = models.CharField(max_length=20, blank=True)
    endereco = models.TextField(blank=True)
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='clientes')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def saldo_devedor(self):
        from financeiro.models import ContaReceber
        from django.db.models import Sum
        total = ContaReceber.objects.filter(
            cliente=self, pago=False
        ).aggregate(total=Sum('valor'))['total']
        return total or 0
