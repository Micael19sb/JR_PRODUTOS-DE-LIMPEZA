from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Produto(models.Model):
    UNIDADE_CHOICES = [
        ('un', 'Unidade'),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    unidade = models.CharField(max_length=10, choices=UNIDADE_CHOICES, default='un')
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']

    def __str__(self):
        return f'{self.codigo} — {self.nome}'

    @property
    def margem(self):
        if self.preco_custo and self.preco_custo > 0:
            return round(((self.preco_venda - self.preco_custo) / self.preco_custo) * 100, 1)
        return None
