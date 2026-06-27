from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from datetime import date, timedelta

from .models import ContaReceber, Despesa, FechamentoCaixa
from vendas.models import Venda


def get_periodo(request):
    hoje = date.today()
    periodo = request.GET.get('periodo', 'mes')
    if periodo == 'hoje':
        inicio = hoje
        fim = hoje
    elif periodo == 'semana':
        inicio = hoje - timedelta(days=hoje.weekday())
        fim = hoje
    elif periodo == 'mes':
        inicio = hoje.replace(day=1)
        fim = hoje
    else:
        inicio = hoje.replace(day=1)
        fim = hoje
    return inicio, fim, periodo


@login_required
def lista(request):
    hoje = date.today()
    inicio, fim, periodo = get_periodo(request)

    contas_pendentes = ContaReceber.objects.filter(pago=False).select_related('cliente').order_by('vencimento')
    total_pendente = contas_pendentes.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    contas_vencidas = [c for c in contas_pendentes if c.vencida]

    vendas = Venda.objects.filter(
        status='concluida',
        criada_em__date__gte=inicio,
        criada_em__date__lte=fim,
    )
    total_entradas = sum(v.total for v in vendas)

    por_pagamento = {}
    for v in vendas:
        forma = v.get_forma_pagamento_display()
        por_pagamento[forma] = por_pagamento.get(forma, Decimal('0')) + v.total

    despesas = Despesa.objects.filter(data__gte=inicio, data__lte=fim)
    total_despesas = despesas.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    lucro = total_entradas - total_despesas
    ultimas_despesas = Despesa.objects.order_by('-data')[:10]

    # Histórico mensal
    todas_vendas = Venda.objects.filter(status='concluida').order_by('criada_em')
    historico_mensal = {}
    for v in todas_vendas:
        chave = v.criada_em.strftime('%Y-%m')
        if chave not in historico_mensal:
            meses = ['Janeiro','Fevereiro','Marco','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
            historico_mensal[chave] = {
                'ano': v.criada_em.year,
                'mes': v.criada_em.month,
                'mes_nome': meses[v.criada_em.month - 1] + '/' + str(v.criada_em.year),
                'total_vendas': Decimal('0'),
                'qtd_vendas': 0,
                'total_despesas': Decimal('0'),
                'lucro': Decimal('0'),
            }
        historico_mensal[chave]['total_vendas'] += v.total
        historico_mensal[chave]['qtd_vendas'] += 1

    todas_despesas = Despesa.objects.all()
    for d in todas_despesas:
        chave = d.data.strftime('%Y-%m')
        if chave in historico_mensal:
            historico_mensal[chave]['total_despesas'] += d.valor

    for chave in historico_mensal:
        h = historico_mensal[chave]
        h['lucro'] = h['total_vendas'] - h['total_despesas']

    historico_lista = sorted(historico_mensal.values(), key=lambda x: (x['ano'], x['mes']), reverse=True)

    context = {
        'hoje': hoje,
        'periodo': periodo,
        'inicio': inicio,
        'fim': fim,
        'contas_pendentes': contas_pendentes,
        'total_pendente': total_pendente,
        'contas_vencidas': len(contas_vencidas),
        'total_entradas': total_entradas,
        'por_pagamento': por_pagamento,
        'total_despesas': total_despesas,
        'lucro': lucro,
        'ultimas_despesas': ultimas_despesas,
        'historico_mensal': historico_lista,
        'categorias': Despesa.CATEGORIA_CHOICES,
    }
    return render(request, 'financeiro/lista.html', context)


@login_required
def fluxo_caixa(request):
    hoje = date.today()
    data_str = request.GET.get('data', str(hoje))
    try:
        data_sel = date.fromisoformat(data_str)
    except:
        data_sel = hoje

    # Buscar fechamento do dia anterior para saldo abertura
    dia_anterior = data_sel - timedelta(days=1)
    fechamento_anterior = FechamentoCaixa.objects.filter(data=dia_anterior).first()
    saldo_abertura = fechamento_anterior.saldo_fechamento if fechamento_anterior else Decimal('0')

    # Vendas do dia
    vendas_dia = Venda.objects.filter(
        status='concluida',
        criada_em__date=data_sel
    ).order_by('criada_em')

    # Despesas do dia
    despesas_dia = Despesa.objects.filter(data=data_sel).order_by('criada_em')

    # Montar movimentacoes em ordem cronologica
    movimentacoes = []
    for v in vendas_dia:
        movimentacoes.append({
            'tipo': 'entrada',
            'hora': v.criada_em.strftime('%H:%M'),
            'descricao': f'Venda #{v.pk} — {v.get_forma_pagamento_display()}',
            'cliente': v.cliente.nome if v.cliente else 'Consumidor final',
            'valor': v.total,
        })
    for d in despesas_dia:
        movimentacoes.append({
            'tipo': 'saida',
            'hora': d.criada_em.strftime('%H:%M') if hasattr(d, 'criada_em') else '00:00',
            'descricao': d.descricao,
            'cliente': d.get_categoria_display(),
            'valor': d.valor,
        })

    movimentacoes.sort(key=lambda x: x['hora'])

    # Totais
    total_entradas = sum(v.total for v in vendas_dia)
    total_saidas = despesas_dia.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saldo_dia = total_entradas - total_saidas
    saldo_acumulado = saldo_abertura + saldo_dia

    # Fechamento do dia
    fechamento_hoje = FechamentoCaixa.objects.filter(data=data_sel).first()

    # Por forma de pagamento
    por_forma = {}
    for v in vendas_dia:
        forma = v.get_forma_pagamento_display()
        por_forma[forma] = por_forma.get(forma, Decimal('0')) + v.total

    context = {
        'hoje': hoje,
        'data_sel': data_sel,
        'saldo_abertura': saldo_abertura,
        'movimentacoes': movimentacoes,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo_dia': saldo_dia,
        'saldo_acumulado': saldo_acumulado,
        'fechamento_hoje': fechamento_hoje,
        'por_forma': por_forma,
        'qtd_vendas': vendas_dia.count(),
    }
    return render(request, 'financeiro/fluxo_caixa.html', context)


@login_required
def fechar_caixa(request):
    if request.method == 'POST':
        data_str = request.POST.get('data')
        saldo_abertura = Decimal(request.POST.get('saldo_abertura', '0').replace(',', '.'))
        total_entradas = Decimal(request.POST.get('total_entradas', '0').replace(',', '.'))
        total_despesas = Decimal(request.POST.get('total_despesas', '0').replace(',', '.'))
        observacao = request.POST.get('observacao', '')

        data_caixa = date.fromisoformat(data_str)
        saldo_fechamento = saldo_abertura + total_entradas - total_despesas

        fechamento, criado = FechamentoCaixa.objects.get_or_create(
            data=data_caixa,
            defaults={
                'saldo_abertura': saldo_abertura,
                'total_entradas': total_entradas,
                'total_despesas': total_despesas,
                'saldo_fechamento': saldo_fechamento,
                'observacao': observacao,
                'fechado': True,
                'criado_por': request.user,
            }
        )
        if not criado:
            fechamento.saldo_abertura = saldo_abertura
            fechamento.total_entradas = total_entradas
            fechamento.total_despesas = total_despesas
            fechamento.saldo_fechamento = saldo_fechamento
            fechamento.observacao = observacao
            fechamento.fechado = True
            fechamento.save()

        messages.success(request, f'Caixa do dia {data_caixa.strftime("%d/%m/%Y")} fechado! Saldo: R$ {saldo_fechamento}')
    return redirect(f'/financeiro/fluxo/?data={data_str}')


@login_required
def dar_baixa(request, pk):
    conta = get_object_or_404(ContaReceber, pk=pk)
    if request.method == 'POST':
        conta.pago = True
        conta.data_pagamento = date.today()
        conta.save()
        messages.success(request, f'Pagamento de {conta.cliente.nome} confirmado! R$ {conta.valor}')
    return redirect('financeiro_lista')


@login_required
def nova_despesa(request):
    if request.method == 'POST':
        descricao = request.POST.get('descricao', '').strip()
        categoria = request.POST.get('categoria', 'outros')
        valor = request.POST.get('valor', '0').replace(',', '.')
        data_desp = request.POST.get('data', str(date.today()))
        observacao = request.POST.get('observacao', '').strip()

        if not descricao or not valor:
            messages.error(request, 'Preencha a descricao e o valor.')
            return redirect('financeiro_lista')

        Despesa.objects.create(
            descricao=descricao,
            categoria=categoria,
            valor=Decimal(valor),
            data=data_desp,
            observacao=observacao,
            criada_por=request.user,
        )
        messages.success(request, f'Despesa "{descricao}" registrada!')
    return redirect('financeiro_lista')


@login_required
def excluir_despesa(request, pk):
    if request.method == 'POST':
        despesa = get_object_or_404(Despesa, pk=pk)
        despesa.delete()
        messages.success(request, 'Despesa excluida.')
    return redirect('financeiro_lista')
