"""
Script para criar dados iniciais do sistema.
Execute com: python manage.py shell < setup_inicial.py
"""
from django.contrib.auth.models import User
from lojas.models import Loja, PerfilUsuario
from produtos.models import Categoria

print("=== Setup Inicial - JR Limpeza de Produtos ===\n")

# 1. Criar loja
print("Criando loja...")
loja, _ = Loja.objects.get_or_create(
    nome="JR Limpeza de Produtos",
    defaults={'cidade': 'Gloria do Goita', 'telefone': '', 'ativa': True}
)
print("  OK: " + str(loja))

# 2. Criar usuario JR
print("\nCriando usuario JR...")
if not User.objects.filter(username='JR').exists():
    user_JR = User.objects.create_superuser('JR', '', '13052023')
    user_JR.first_name = 'JR'
    user_JR.save()
    PerfilUsuario.objects.create(user=user_JR, is_dono=True, loja=loja)
    print("  OK: JR / 13052023")
else:
    u = User.objects.get(username='JR')
    u.set_password('13052023')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print("  OK: senha do usuario JR redefinida para 13052023")

# 3. Criar categorias
print("\nCriando categorias...")
categorias = [
    'Amaciante',
    'Alvejante',
    'Cloro',
    'Desengordurante',
    'Desinfetante',
    'Detergente',
    'Agua Sanitaria',
    'Inflamavel',
    'Lava Roupa',
    'Limpa Piso',
    'Limpeza Geral',
    'Pastilha de Cloro',
    'Polidor',
    'Sabao em Po / Liquido',
]
for nome in categorias:
    cat, criado = Categoria.objects.get_or_create(nome=nome)
    if criado:
        print("  OK: " + nome)
    else:
        print("  Ja existe: " + nome)

print("\n=== Setup concluido! ===")
print("\nAcesse: http://localhost:8000")
print("Login: JR / 13052023")
print("Admin Django: http://localhost:8000/admin")
print("\nCadastre os produtos em: Estoque > Cadastrar produto")
