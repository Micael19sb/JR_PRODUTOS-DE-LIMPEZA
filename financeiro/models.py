from django.db import models
from clientes.models import Cliente
from vendas.models import Venda


class ContaReceber(models.Model):
    venda = models.OneToOneField(Venda, on_delete=models.CASCADE, related_name='conta_receber', null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contas')
    descricao = models.CharField(max_length=200, default='Venda a prazo')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField()
    pago = models.BooleanField(default=False)
    data_pagamento = models.DateField(null=True, blank=True)
    observacao = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Conta a receber'
        verbose_name_plural = 'Contas a receber'
        ordering = ['vencimento']

    def __str__(self):
        status = 'PAGO' if self.pago else 'PENDENTE'
        return f'{self.cliente.nome} | R$ {self.valor} | {self.vencimento} | {status}'

    @property
    def vencida(self):
        from django.utils import timezone
        if self.pago:
            return False
        return self.vencimento < timezone.now().date()


class Despesa(models.Model):
    CATEGORIA_CHOICES = [
        ('aluguel', 'Aluguel'),
        ('energia', 'Energia eletrica'),
        ('agua', 'Agua'),
        ('telefone', 'Telefone / Internet'),
        ('fornecedor', 'Fornecedor / Mercadoria'),
        ('funcionario', 'Funcionario / Salario'),
        ('transporte', 'Transporte / Frete'),
        ('outros', 'Outros'),
    ]

    descricao = models.CharField(max_length=200)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='outros')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    observacao = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    criada_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'
        ordering = ['-data']

    def __str__(self):
        return f'{self.descricao} | R$ {self.valor} | {self.data}'


class FechamentoCaixa(models.Model):
    data = models.DateField(unique=True)
    saldo_abertura = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_entradas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_despesas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_fechamento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacao = models.TextField(blank=True)
    fechado = models.BooleanField(default=False)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Fechamento de caixa'
        verbose_name_plural = 'Fechamentos de caixa'
        ordering = ['-data']

    def __str__(self):
        return f'Caixa {self.data} | Saldo: R$ {self.saldo_fechamento}'
