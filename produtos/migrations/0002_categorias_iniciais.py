from django.db import migrations


CATEGORIAS = [
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
    'Vonixx',
]


def criar_categorias(apps, schema_editor):
    Categoria = apps.get_model('produtos', 'Categoria')
    for nome in CATEGORIAS:
        Categoria.objects.get_or_create(nome=nome)


def remover_categorias(apps, schema_editor):
    Categoria = apps.get_model('produtos', 'Categoria')
    Categoria.objects.filter(nome__in=CATEGORIAS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(criar_categorias, remover_categorias),
    ]
