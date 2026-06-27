from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

from vendas.models import Venda
from estoque.models import Estoque
from financeiro.models import ContaReceber
from lojas.models import Loja


@login_required
def dashboard(request):
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)

    vendas_qs = Venda.objects.filter(status='concluida')
    estoques_qs = Estoque.objects.all()
    contas_qs = ContaReceber.objects.exclude(status='quitado')
    lojas = Loja.objects.filter(ativa=True)

    # Totais do dia
    vendas_hoje = vendas_qs.filter(criada_em__date=hoje)
    total_hoje = sum(v.total for v in vendas_hoje)

    # Totais do mês
    vendas_mes = vendas_qs.filter(criada_em__date__gte=inicio_mes)
    total_mes = sum(v.total for v in vendas_mes)

    # A receber: contas a receber cadastradas + vendas fiado sem conta gerada
    total_contas = contas_qs.aggregate(t=Sum('valor'))['t'] or Decimal('0')

    # Vendas fiado que não geraram ContaReceber (ex: consumidor final)
    vendas_fiado_sem_conta = vendas_qs.filter(
        forma_pagamento='fiado'
    ).exclude(
        conta_receber__isnull=False
    )
    total_fiado_avulso = sum(v.total for v in vendas_fiado_sem_conta)

    total_receber = total_contas + total_fiado_avulso
    contas_vencidas = sum(1 for c in contas_qs if c.vencida)

    # Alertas de estoque
    alertas_estoque = [e for e in estoques_qs.select_related('produto', 'loja') if e.abaixo_minimo]

    # Últimas vendas
    ultimas_vendas = vendas_qs.order_by('-criada_em')[:10].select_related('cliente', 'loja', 'criada_por')

    # Clientes devedores
    from clientes.models import Cliente
    clientes_devedores = []
    for cliente in Cliente.objects.filter(ativo=True).order_by('nome'):
        saldo = cliente.saldo_devedor
        if saldo > 0:
            # Verificar se tem conta vencida
            tem_vencida = any(c.vencida for c in cliente.contas.exclude(status='quitado'))
            clientes_devedores.append({
                'cliente': cliente,
                'saldo': saldo,
                'vencida': tem_vencida,
            })
    clientes_devedores.sort(key=lambda x: x['vencida'], reverse=True)

    context = {
        'total_hoje': total_hoje,
        'qtd_hoje': vendas_hoje.count(),
        'total_mes': total_mes,
        'qtd_mes': vendas_mes.count(),
        'total_receber': total_receber,
        'contas_vencidas': contas_vencidas,
        'alertas_estoque': alertas_estoque,
        'ultimas_vendas': ultimas_vendas,
        'clientes_devedores': clientes_devedores,
        'is_dono': True,
    }
    return render(request, 'dashboard/dashboard.html', context)
