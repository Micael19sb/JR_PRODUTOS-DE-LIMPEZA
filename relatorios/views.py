from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count
from decimal import Decimal
from datetime import date, timedelta
import json

from vendas.models import Venda, ItemVenda
from estoque.models import Estoque
from financeiro.models import ContaReceber, Despesa
from lojas.models import Loja
from produtos.models import Produto


@login_required
def dashboard(request):
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)

    vendas_qs = Venda.objects.filter(status='concluida')
    estoques_qs = Estoque.objects.all()
    contas_qs = ContaReceber.objects.filter(pago=False)
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
            tem_vencida = any(c.vencida for c in cliente.contas.filter(pago=False))
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


@login_required
def relatorio_mensal(request):
    hoje = timezone.now().date()

    # Período selecionado
    mes = int(request.GET.get('mes', hoje.month))
    ano = int(request.GET.get('ano', hoje.year))

    import calendar
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])

    meses_nomes = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                   'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    mes_nome = meses_nomes[mes - 1]

    # Vendas do período
    vendas = Venda.objects.filter(
        status='concluida',
        criada_em__date__gte=primeiro_dia,
        criada_em__date__lte=ultimo_dia,
    )
    total_vendas = sum(v.total for v in vendas)
    qtd_vendas = vendas.count()

    # Despesas do período
    despesas = Despesa.objects.filter(data__gte=primeiro_dia, data__lte=ultimo_dia)
    total_despesas = despesas.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    lucro = total_vendas - total_despesas

    # Por forma de pagamento
    por_pagamento = {}
    for v in vendas:
        forma = v.get_forma_pagamento_display()
        por_pagamento[forma] = float(por_pagamento.get(forma, 0)) + float(v.total)

    # Top 10 produtos mais vendidos
    top_produtos = ItemVenda.objects.filter(
        venda__status='concluida',
        venda__criada_em__date__gte=primeiro_dia,
        venda__criada_em__date__lte=ultimo_dia,
    ).values('produto__nome').annotate(
        total_qtd=Sum('quantidade'),
        total_valor=Sum('subtotal'),
    ).order_by('-total_qtd')[:10]

    # Produtos sem nenhuma venda no período
    ids_vendidos = ItemVenda.objects.filter(
        venda__status='concluida',
        venda__criada_em__date__gte=primeiro_dia,
        venda__criada_em__date__lte=ultimo_dia,
    ).values_list('produto_id', flat=True).distinct()

    produtos_parados = Produto.objects.filter(
        ativo=True
    ).exclude(
        pk__in=ids_vendidos
    ).order_by('nome')

    # Faturamento diário (para gráfico de linha)
    faturamento_diario = {}
    for v in vendas:
        dia = v.criada_em.strftime('%d/%m')
        faturamento_diario[dia] = float(faturamento_diario.get(dia, 0)) + float(v.total)
    dias_labels = list(faturamento_diario.keys())
    dias_valores = list(faturamento_diario.values())

    # Histórico dos últimos 6 meses
    historico = []
    for i in range(5, -1, -1):
        d = hoje.replace(day=1) - timedelta(days=1)
        for _ in range(i):
            d = d.replace(day=1) - timedelta(days=1)
        m_inicio = date(d.year, d.month, 1)
        m_fim = date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
        v_mes = Venda.objects.filter(status='concluida', criada_em__date__gte=m_inicio, criada_em__date__lte=m_fim)
        total_m = float(sum(v.total for v in v_mes))
        desp_m = float(Despesa.objects.filter(data__gte=m_inicio, data__lte=m_fim).aggregate(t=Sum('valor'))['t'] or 0)
        historico.append({
            'mes': meses_nomes[d.month - 1][:3] + '/' + str(d.year)[-2:],
            'faturamento': total_m,
            'despesas': desp_m,
            'lucro': total_m - desp_m,
        })

    # Gerar lista de meses/anos disponíveis para filtro
    opcoes_periodo = []
    for i in range(11, -1, -1):
        d = hoje.replace(day=1)
        for _ in range(i):
            d = (d - timedelta(days=1)).replace(day=1)
        opcoes_periodo.append({
            'mes': d.month,
            'ano': d.year,
            'label': meses_nomes[d.month - 1] + '/' + str(d.year),
            'selecionado': d.month == mes and d.year == ano,
        })

    context = {
        'mes_nome': mes_nome,
        'ano': ano,
        'mes': mes,
        'primeiro_dia': primeiro_dia,
        'ultimo_dia': ultimo_dia,
        'total_vendas': total_vendas,
        'qtd_vendas': qtd_vendas,
        'total_despesas': total_despesas,
        'lucro': lucro,
        'por_pagamento': por_pagamento,
        'top_produtos': top_produtos,
        'produtos_parados': produtos_parados,
        'dias_labels': json.dumps(dias_labels),
        'dias_valores': json.dumps(dias_valores),
        'historico': historico,
        'historico_labels': json.dumps([h['mes'] for h in historico]),
        'historico_faturamento': json.dumps([h['faturamento'] for h in historico]),
        'historico_despesas': json.dumps([h['despesas'] for h in historico]),
        'historico_lucro': json.dumps([h['lucro'] for h in historico]),
        'pagamento_labels': json.dumps(list(por_pagamento.keys())),
        'pagamento_valores': json.dumps(list(por_pagamento.values())),
        'top_nomes': json.dumps([p['produto__nome'] for p in top_produtos]),
        'top_qtds': json.dumps([float(p['total_qtd']) for p in top_produtos]),
        'top_valores': json.dumps([float(p['total_valor']) for p in top_produtos]),
        'opcoes_periodo': opcoes_periodo,
    }
    return render(request, 'relatorios/relatorio.html', context)
