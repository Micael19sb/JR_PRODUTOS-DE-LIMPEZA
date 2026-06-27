from django.db import models
from django.db.models import Sum
from lojas.models import Loja
from produtos.models import Produto
from clientes.models import Cliente


class Venda(models.Model):
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('pix', 'PIX'),
        ('cartao_debito', 'Cartão de Débito'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('fiado', 'Fiado'),
        ('boleto', 'Boleto'),
    ]

    STATUS_CHOICES = [
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]

    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='vendas')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendas')
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='concluida')
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacao = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    criada_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering = ['-criada_em']

    def __str__(self):
        return f'Venda #{self.pk} — {self.loja.cidade} — {self.criada_em.strftime("%d/%m/%Y %H:%M")}'

    @property
    def subtotal(self):
        return self.itens.aggregate(total=Sum('subtotal'))['total'] or 0

    @property
    def total(self):
        return self.subtotal - self.desconto


class ItemVenda(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item da venda'
        verbose_name_plural = 'Itens da venda'

    def __str__(self):
        return f'{self.produto.nome} x {self.quantidade}'

    def save(self, *args, **kwargs):
        self.subtotal = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)
