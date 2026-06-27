from django.db import models
from django.contrib.auth.models import User


class Loja(models.Model):
    nome = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.TextField(blank=True)
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Loja'
        verbose_name_plural = 'Lojas'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} — {self.cidade}'


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    loja = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True)
    is_dono = models.BooleanField(default=False, help_text='Dono vê todas as lojas')

    class Meta:
        verbose_name = 'Perfil de usuário'
        verbose_name_plural = 'Perfis de usuários'

    def __str__(self):
        return f'{self.user.username} — {self.loja or "Todas as lojas"}'
