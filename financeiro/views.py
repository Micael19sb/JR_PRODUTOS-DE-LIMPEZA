from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from datetime import date, timedelta

from .models import MovimentoCaixa, ContaReceber, Despesa, FechamentoCaixa
from vendas.models import Venda


@login_required
def lista(request):
    """Painel financeiro principal."""
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)

    # Saldo atual do caixa (soma de todos os movimentos)
    entradas = MovimentoCaixa.objects.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saidas = MovimentoCaixa.objects.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saldo_atual = entradas - saidas

    # Contas a receber pendentes
    contas_pendentes = ContaReceber.objects.exclude(status='quitado').select_related('cliente').order_by('vencimento')
    total_a_receber = sum(c.valor_pendente for c in contas_pendentes)
    contas_vencidas = [c for c in contas_pendentes if c.vencida]

    # Despesas do mês
    despesas_mes = Despesa.objects.filter(data__gte=inicio_mes, pago=True)
    total_despesas_mes = despesas_mes.aggregate(t=Sum('valor'))['t'] or Decimal('0')

    # Entradas do mês
    entradas_mes = MovimentoCaixa.objects.filter(tipo='entrada', data__gte=inicio_mes).aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saidas_mes = MovimentoCaixa.objects.filter(tipo='saida', data__gte=inicio_mes).aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saldo_mes = entradas_mes - saidas_mes

    # Últimas movimentações
    ultimas_movimentacoes = MovimentoCaixa.objects.select_related('usuario', 'venda', 'conta_receber').order_by('-criado_em')[:15]

    # Últimas despesas
    ultimas_despesas = Despesa.objects.order_by('-data')[:8]

    # Histórico mensal
    todos_movimentos = MovimentoCaixa.objects.all()
    historico_mensal = {}
    for m in todos_movimentos:
        chave = m.data.strftime('%Y-%m')
        if chave not in historico_mensal:
            meses = ['Janeiro','Fevereiro','Marco','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
            historico_mensal[chave] = {
                'ano': m.data.year, 'mes': m.data.month,
                'mes_nome': meses[m.data.month - 1] + '/' + str(m.data.year),
                'entradas': Decimal('0'), 'saidas': Decimal('0'),
            }
        if m.tipo == 'entrada':
            historico_mensal[chave]['entradas'] += m.valor
        else:
            historico_mensal[chave]['saidas'] += m.valor

    for chave in historico_mensal:
        h = historico_mensal[chave]
        h['saldo'] = h['entradas'] - h['saidas']

    historico_lista = sorted(historico_mensal.values(), key=lambda x: (x['ano'], x['mes']), reverse=True)

    context = {
        'hoje': hoje,
        'saldo_atual': saldo_atual,
        'total_a_receber': total_a_receber,
        'contas_pendentes': contas_pendentes,
        'contas_vencidas': len(contas_vencidas),
        'total_despesas_mes': total_despesas_mes,
        'entradas_mes': entradas_mes,
        'saidas_mes': saidas_mes,
        'saldo_mes': saldo_mes,
        'ultimas_movimentacoes': ultimas_movimentacoes,
        'ultimas_despesas': ultimas_despesas,
        'historico_mensal': historico_lista,
        'categorias': Despesa.CATEGORIA_CHOICES,
    }
    return render(request, 'financeiro/lista.html', context)


@login_required
def fluxo_caixa(request):
    """Fluxo de caixa do dia."""
    hoje = date.today()
    data_str = request.GET.get('data', str(hoje))
    try:
        data_sel = date.fromisoformat(data_str)
    except:
        data_sel = hoje

    movimentos = MovimentoCaixa.objects.filter(data=data_sel).select_related('usuario', 'venda', 'conta_receber').order_by('criado_em')
    total_entradas = movimentos.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    total_saidas = movimentos.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saldo_dia = total_entradas - total_saidas
    fechamento = FechamentoCaixa.objects.filter(data=data_sel).first()

    # Por forma de pagamento
    por_forma = {}
    for m in movimentos.filter(tipo='entrada'):
        forma = m.forma_pagamento or 'Outros'
        por_forma[forma] = por_forma.get(forma, Decimal('0')) + m.valor

    context = {
        'hoje': hoje,
        'data_sel': data_sel,
        'movimentos': movimentos,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo_dia': saldo_dia,
        'fechamento': fechamento,
        'por_forma': por_forma,
    }
    return render(request, 'financeiro/fluxo_caixa.html', context)


@login_required
def previsao_caixa(request):
    """Previsão de caixa para os próximos 30 dias."""
    hoje = date.today()
    fim = hoje + timedelta(days=30)

    # Saldo atual
    entradas = MovimentoCaixa.objects.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saidas = MovimentoCaixa.objects.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or Decimal('0')
    saldo_atual = entradas - saidas

    # Contas a receber previstas
    contas_previstas = ContaReceber.objects.exclude(status='quitado').filter(
        vencimento__gte=hoje, vencimento__lte=fim
    ).select_related('cliente').order_by('vencimento')
    total_previsto_receber = sum(c.valor_pendente for c in contas_previstas)

    # Despesas futuras não pagas
    despesas_futuras = Despesa.objects.filter(data__gte=hoje, data__lte=fim, pago=False).order_by('data')
    total_previsto_pagar = despesas_futuras.aggregate(t=Sum('valor'))['t'] or Decimal('0')

    # Saldo projetado
    saldo_projetado = saldo_atual + total_previsto_receber - total_previsto_pagar

    # Timeline dos próximos 30 dias
    timeline = []
    saldo_acum = saldo_atual
    for i in range(30):
        dia = hoje + timedelta(days=i)
        entradas_dia = sum(c.valor_pendente for c in contas_previstas if c.vencimento == dia)
        saidas_dia = sum(d.valor for d in despesas_futuras if d.data == dia)
        saldo_acum += entradas_dia - saidas_dia
        if entradas_dia > 0 or saidas_dia > 0:
            timeline.append({
                'data': dia,
                'entradas': entradas_dia,
                'saidas': saidas_dia,
                'saldo': saldo_acum,
            })

    context = {
        'hoje': hoje,
        'fim': fim,
        'saldo_atual': saldo_atual,
        'contas_previstas': contas_previstas,
        'total_previsto_receber': total_previsto_receber,
        'despesas_futuras': despesas_futuras,
        'total_previsto_pagar': total_previsto_pagar,
        'saldo_projetado': saldo_projetado,
        'timeline': timeline,
    }
    return render(request, 'financeiro/previsao.html', context)


@login_required
def receber_pagamento(request, pk):
    """Registra pagamento parcial ou total de uma conta a receber."""
    conta = get_object_or_404(ContaReceber, pk=pk)

    if request.method == 'POST':
        valor_str = request.POST.get('valor', '0').replace(',', '.')
        try:
            valor = Decimal(valor_str)
        except:
            messages.error(request, 'Valor invalido.')
            return redirect('financeiro_lista')

        if valor <= 0 or valor > conta.valor_pendente:
            messages.error(request, f'Valor deve ser entre R$ 0,01 e R$ {conta.valor_pendente}.')
            return redirect('financeiro_lista')

        # Registrar entrada no caixa
        MovimentoCaixa.objects.create(
            data=date.today(),
            tipo='entrada',
            categoria='recebimento_fiado',
            descricao=f'Recebimento de {conta.cliente.nome} — {conta.descricao}',
            valor=valor,
            forma_pagamento=request.POST.get('forma_pagamento', 'dinheiro'),
            usuario=request.user,
            conta_receber=conta,
        )

        # Atualizar conta
        conta.valor_pago += valor
        if conta.valor_pago >= conta.valor_total:
            conta.status = 'quitado'
            conta.valor_pago = conta.valor_total
        else:
            conta.status = 'parcial'
        conta.save()

        messages.success(request, f'Pagamento de R$ {valor} de {conta.cliente.nome} registrado!')

    return redirect('financeiro_lista')


@login_required
def nova_despesa(request):
    if request.method == 'POST':
        descricao = request.POST.get('descricao', '').strip()
        categoria = request.POST.get('categoria', 'outros')
        valor_str = request.POST.get('valor', '0').replace(',', '.')
        data_desp = request.POST.get('data', str(date.today()))
        observacao = request.POST.get('observacao', '').strip()
        pago = request.POST.get('pago') == 'on'

        if not descricao or not valor_str:
            messages.error(request, 'Preencha descricao e valor.')
            return redirect('financeiro_lista')

        valor = Decimal(valor_str)
        despesa = Despesa.objects.create(
            descricao=descricao, categoria=categoria,
            valor=valor, data=data_desp,
            pago=pago, observacao=observacao,
            criada_por=request.user,
        )

        # Se já pago, registrar saída no caixa
        if pago:
            MovimentoCaixa.objects.create(
                data=date.fromisoformat(data_desp),
                tipo='saida',
                categoria='despesa',
                descricao=descricao,
                valor=valor,
                forma_pagamento='dinheiro',
                usuario=request.user,
                despesa_ref=despesa,
            )

        messages.success(request, f'Despesa "{descricao}" registrada!')
    return redirect('financeiro_lista')


@login_required
def excluir_despesa(request, pk):
    if request.method == 'POST':
        despesa = get_object_or_404(Despesa, pk=pk)
        # Remover movimento de caixa relacionado
        MovimentoCaixa.objects.filter(despesa_ref=despesa).delete()
        despesa.delete()
        messages.success(request, 'Despesa excluida.')
    return redirect('financeiro_lista')


@login_required
def fechar_caixa(request):
    if request.method == 'POST':
        data_str = request.POST.get('data')
        observacao = request.POST.get('observacao', '')
        data_caixa = date.fromisoformat(data_str)

        movimentos = MovimentoCaixa.objects.filter(data=data_caixa)
        total_entradas = movimentos.filter(tipo='entrada').aggregate(t=Sum('valor'))['t'] or Decimal('0')
        total_saidas = movimentos.filter(tipo='saida').aggregate(t=Sum('valor'))['t'] or Decimal('0')
        saldo = total_entradas - total_saidas

        FechamentoCaixa.objects.update_or_create(
            data=data_caixa,
            defaults={
                'saldo_abertura': Decimal('0'),
                'total_entradas': total_entradas,
                'total_despesas': total_saidas,
                'saldo_fechamento': saldo,
                'observacao': observacao,
                'fechado': True,
                'criado_por': request.user,
            }
        )
        messages.success(request, f'Caixa de {data_caixa.strftime("%d/%m/%Y")} fechado! Saldo: R$ {saldo}')
    return redirect(f'/financeiro/fluxo/?data={data_str}')


@login_required
def enviar_relatorio(request):
    if request.method == 'POST':
        from .relatorio import gerar_relatorio_mensal
        mes = int(request.POST.get('mes', date.today().month))
        ano = int(request.POST.get('ano', date.today().year))
        email_destino = request.POST.get('email', '').strip()
        if not email_destino:
            messages.error(request, 'Informe um email.')
            return redirect('financeiro_lista')
        try:
            dados = gerar_relatorio_mensal(ano, mes, email_destino)
            messages.success(request, f'Relatorio enviado para {email_destino}!')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    return redirect('financeiro_lista')
