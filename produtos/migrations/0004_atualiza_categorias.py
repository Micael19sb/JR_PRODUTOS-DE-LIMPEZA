from django.db import migrations


CATEGORIAS_FINAIS = [
    'Água Sanitária',
    'Amaciante',
    'Automotivo',
    'Desinfetante',
    'Desinfetante Casa Km',
    'Essências',
    'Home Spray',
    'Inflamável',
    'Inseticida e Controle de Pragas',
    'Lava-louça',
    'Lava-roupa em Pó',
    'Lava-roupa Líquido',
    'Matéria-Prima',
    'Material de Limpeza',
    'Piscina',
    'Polidor',
    'Sabonete Líquido',
    'Utilidades',
    'Valença',
    'Vonixx',
]


def atualizar_categorias(apps, schema_editor):
    Categoria = apps.get_model('produtos', 'Categoria')
    # Não apaga nada — só cria as que ainda não existem
    for nome in CATEGORIAS_FINAIS:
        Categoria.objects.get_or_create(nome=nome)


def reverter(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0003_reset_categorias'),
    ]

    operations = [
        migrations.RunPython(atualizar_categorias, reverter),
    ]
