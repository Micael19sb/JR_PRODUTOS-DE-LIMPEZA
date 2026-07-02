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
    'Vonixx',
]


def reset_categorias(apps, schema_editor):
    Categoria = apps.get_model('produtos', 'Categoria')
    # Apaga TODAS as categorias existentes
    Categoria.objects.all().delete()
    # Recria apenas as corretas
    for nome in CATEGORIAS_FINAIS:
        Categoria.objects.create(nome=nome)


def reverter(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0002_categorias_iniciais'),
    ]

    operations = [
        migrations.RunPython(reset_categorias, reverter),
    ]
