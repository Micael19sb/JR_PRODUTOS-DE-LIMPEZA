from django.db import models
from django.utils import timezone
from decimal import Decimal


class MovimentoCaixa(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saida'),
    ]
    CATEGORIA_CHOICES = [
        ('venda_avista', 'Venda a vista'),
        ('recebimento_fiado', 'Recebimento de fiado'),
        ('despesa', 'Despesa'),
        ('troco', 'Troco'),
        ('outros', 'Outros'),
    ]

    data = models.DateField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES)
    descricao = models.CharField(max_length=300)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField(max_length=50, blank=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    venda = models.ForeignKey('vendas.Venda', on_delete=models.SET_NULL, null=True, blank=True, related_name='movimentos_caixa')
    conta_receber = models.ForeignKey('ContaReceber', on_delete=models.SET_NULL, null=True, blank=True, related_name='movimentos')
    despesa_ref = models.ForeignKey('Despesa', on_delete=models.SET_NULL, null=True, blank=True, related_name='movimentos')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-criado_em']
        verbose_name = 'Movimento de caixa'
        verbose_name_plural = 'Movimentos de caixa'

    def __str__(self):
        return f'{self.tipo} | {self.descricao} | R$ {self.valor}'


class ContaReceber(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('parcial', 'Parcialmente pago'),
        ('quitado', 'Quitado'),
    ]

    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE, related_name='contas')
    venda = models.OneToOneField('vendas.Venda', on_delete=models.CASCADE, related_name='conta_receber', null=True, blank=True)
    descricao = models.CharField(max_length=200, default='Venda a prazo')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vencimento = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    observacao = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['vencimento']
        verbose_name = 'Conta a receber'
        verbose_name_plural = 'Contas a receber'

    def __str__(self):
        return f'{self.cliente.nome} | R$ {self.valor_pendente} | {self.status}'

    @property
    def valor_pendente(self):
        return self.valor_total - self.valor_pago

    @property
    def pago(self):
        return self.status == 'quitado'

    @property
    def vencida(self):
        if self.status == 'quitado':
            return False
        from django.utils import timezone
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
    pago = models.BooleanField(default=True)
    observacao = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    criada_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-data']
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'

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
        ordering = ['-data']
        verbose_name = 'Fechamento de caixa'
        verbose_name_plural = 'Fechamentos de caixa'
