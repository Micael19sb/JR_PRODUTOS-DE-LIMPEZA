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


def limpar_e_recriar(apps, schema_editor):
    Categoria = apps.get_model('produtos', 'Categoria')
    Categoria.objects.exclude(nome__in=CATEGORIAS_FINAIS).delete()
    for nome in CATEGORIAS_FINAIS:
        Categoria.objects.get_or_create(nome=nome)


def reverter(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(limpar_e_recriar, reverter),
    ]
