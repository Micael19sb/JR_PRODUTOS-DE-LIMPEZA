from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from datetime import date, timedelta
from collections import defaultdict

from .models import ContaReceber, Despesa
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

    # Contas a receber pendentes
    contas_pendentes = ContaReceber.objects.filter(pago=False).select_related('cliente').order_by('vencimento')
    total_pendente = contas_pendentes.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    contas_vencidas = [c for c in contas_pendentes if c.vencida]

    # Entradas do período
    vendas = Venda.objects.filter(
        status='concluida',
        criada_em__date__gte=inicio,
        criada_em__date__lte=fim,
    )
    total_entradas = sum(v.total for v in vendas)

    # Por forma de pagamento
    por_pagamento = {}
    for v in vendas:
        forma = v.get_forma_pagamento_display()
        por_pagamento[forma] = por_pagamento.get(forma, Decimal('0')) + v.total

    # Despesas do período
    despesas = Despesa.objects.filter(data__gte=inicio, data__lte=fim)
    total_despesas = despesas.aggregate(t=Sum('valor'))['t'] or Decimal('0')

    # Lucro real
    lucro = total_entradas - total_despesas

    # Últimas despesas
    ultimas_despesas = Despesa.objects.order_by('-data')[:10]

    # === HISTÓRICO MENSAL ===
    # Buscar todas as vendas agrupadas por mês/ano
    todas_vendas = Venda.objects.filter(status='concluida').order_by('criada_em')
    historico_mensal = {}

    for v in todas_vendas:
        chave = v.criada_em.strftime('%Y-%m')
        if chave not in historico_mensal:
            historico_mensal[chave] = {
                'ano': v.criada_em.year,
                'mes': v.criada_em.month,
                'mes_nome': ['Janeiro','Fevereiro','Marco','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'][v.criada_em.month - 1] + '/' + str(v.criada_em.year),
                'total_vendas': Decimal('0'),
                'qtd_vendas': 0,
                'total_despesas': Decimal('0'),
                'lucro': Decimal('0'),
            }
        historico_mensal[chave]['total_vendas'] += v.total
        historico_mensal[chave]['qtd_vendas'] += 1

    # Adicionar despesas por mês
    todas_despesas = Despesa.objects.all()
    for d in todas_despesas:
        chave = d.data.strftime('%Y-%m')
        if chave in historico_mensal:
            historico_mensal[chave]['total_despesas'] += d.valor

    # Calcular lucro por mês
    for chave in historico_mensal:
        h = historico_mensal[chave]
        h['lucro'] = h['total_vendas'] - h['total_despesas']

    # Ordenar do mais recente para o mais antigo
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
