from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('clientes', '0001_initial'),
        ('vendas', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Despesa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=200)),
                ('categoria', models.CharField(choices=[('aluguel', 'Aluguel'), ('energia', 'Energia eletrica'), ('agua', 'Agua'), ('telefone', 'Telefone / Internet'), ('fornecedor', 'Fornecedor / Mercadoria'), ('funcionario', 'Funcionario / Salario'), ('transporte', 'Transporte / Frete'), ('outros', 'Outros')], default='outros', max_length=20)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('data', models.DateField()),
                ('pago', models.BooleanField(default=True)),
                ('observacao', models.TextField(blank=True)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('criada_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={'verbose_name': 'Despesa', 'verbose_name_plural': 'Despesas', 'ordering': ['-data']},
        ),
        migrations.CreateModel(
            name='FechamentoCaixa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(unique=True)),
                ('saldo_abertura', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_entradas', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_despesas', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('saldo_fechamento', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('observacao', models.TextField(blank=True)),
                ('fechado', models.BooleanField(default=False)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('criado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={'verbose_name': 'Fechamento de caixa', 'verbose_name_plural': 'Fechamentos de caixa', 'ordering': ['-data']},
        ),
        migrations.CreateModel(
            name='ContaReceber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(default='Venda a prazo', max_length=200)),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('valor_pago', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('vencimento', models.DateField()),
                ('status', models.CharField(choices=[('pendente', 'Pendente'), ('parcial', 'Parcialmente pago'), ('quitado', 'Quitado')], default='pendente', max_length=10)),
                ('observacao', models.TextField(blank=True)),
                ('criada_em', models.DateTimeField(auto_now_add=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contas', to='clientes.cliente')),
                ('venda', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='conta_receber', to='vendas.venda')),
            ],
            options={'verbose_name': 'Conta a receber', 'verbose_name_plural': 'Contas a receber', 'ordering': ['vencimento']},
        ),
        migrations.CreateModel(
            name='MovimentoCaixa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(default=django.utils.timezone.now)),
                ('tipo', models.CharField(choices=[('entrada', 'Entrada'), ('saida', 'Saida')], max_length=10)),
                ('categoria', models.CharField(choices=[('venda_avista', 'Venda a vista'), ('recebimento_fiado', 'Recebimento de fiado'), ('despesa', 'Despesa'), ('troco', 'Troco'), ('outros', 'Outros')], max_length=30)),
                ('descricao', models.CharField(max_length=300)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('forma_pagamento', models.CharField(blank=True, max_length=50)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('conta_receber', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentos', to='financeiro.contareceber')),
                ('despesa_ref', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentos', to='financeiro.despesa')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
                ('venda', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentos_caixa', to='vendas.venda')),
            ],
            options={'verbose_name': 'Movimento de caixa', 'verbose_name_plural': 'Movimentos de caixa', 'ordering': ['-data', '-criado_em']},
        ),
    ]
