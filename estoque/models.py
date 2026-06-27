from django.db import models
from lojas.models import Loja
from produtos.models import Produto


class Estoque(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='estoques')
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='estoques')
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=5)

    class Meta:
        verbose_name = 'Estoque'
        verbose_name_plural = 'Estoques'
        unique_together = ('produto', 'loja')

    def __str__(self):
        return f'{self.produto.nome} | {self.loja.cidade} | {self.quantidade}'

    @property
    def abaixo_minimo(self):
        return self.quantidade <= self.estoque_minimo


class MovimentoEstoque(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída (venda)'),
        ('ajuste', 'Ajuste manual'),
        ('transferencia', 'Transferência entre lojas'),
    ]

    estoque = models.ForeignKey(Estoque, on_delete=models.CASCADE, related_name='movimentos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Movimento de estoque'
        verbose_name_plural = 'Movimentos de estoque'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.tipo} | {self.estoque.produto.nome} | {self.quantidade}'
