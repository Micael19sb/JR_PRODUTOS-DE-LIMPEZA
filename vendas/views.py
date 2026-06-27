import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Venda, ItemVenda
from produtos.models import Produto
from clientes.models import Cliente
from estoque.models import Estoque, MovimentoEstoque
from financeiro.models import ContaReceber
from lojas.models import Loja

from datetime import date, timedelta


def get_loja():
    return Loja.objects.filter(ativa=True).first()


@login_required
def pdv(request):
    loja = get_loja()
    # Todos os clientes ativos com info de saldo devedor
    clientes_qs = Cliente.objects.filter(ativo=True).order_by('nome')
    clientes = []
    for c in clientes_qs:
        c.tem_divida = c.saldo_devedor > 0
        clientes.append(c)

    # Produtos com estoque disponível
    produtos = Produto.objects.filter(ativo=True).select_related('categoria').order_by('categoria__nome', 'nome')
    for p in produtos:
        try:
            est = Estoque.objects.get(produto=p, loja=loja)
            p.estoque_disp = float(est.quantidade)
        except Estoque.DoesNotExist:
            p.estoque_disp = 0

    context = {
        'loja': loja,
        'clientes': clientes,
        'produtos': produtos,
        'formas_pagamento': Venda.FORMA_PAGAMENTO_CHOICES,
    }
    return render(request, 'pdv/pdv.html', context)


@login_required
def buscar_produto(request):
    q = request.GET.get('q', '').strip()
    loja = get_loja()
    resultados = []

    if q and loja:
        produtos = (
            Produto.objects.filter(ativo=True, nome__icontains=q) |
            Produto.objects.filter(ativo=True, codigo__icontains=q)
        ).distinct()[:10]

        for p in produtos:
            try:
                est = Estoque.objects.get(produto=p, loja=loja)
                qtd_estoque = float(est.quantidade)
            except Estoque.DoesNotExist:
                qtd_estoque = 0

            resultados.append({
                'id': p.pk,
                'codigo': p.codigo,
                'nome': p.nome,
                'preco': float(p.preco_venda),
                'unidade': p.unidade,
                'estoque': qtd_estoque,
            })

    return JsonResponse({'produtos': resultados})


@login_required
@require_POST
@transaction.atomic
def finalizar_venda(request):
    try:
        data = json.loads(request.body)
        itens = data.get('itens', [])
        forma_pagamento = data.get('forma_pagamento')
        cliente_id = data.get('cliente_id')
        desconto = Decimal(str(data.get('desconto', 0)))
        vencimento_fiado = data.get('vencimento_fiado')
        valor_recebido = data.get('valor_recebido')
        troco = data.get('troco')

        if not itens:
            return JsonResponse({'erro': 'Carrinho vazio'}, status=400)

        loja = get_loja()
        cliente = Cliente.objects.get(pk=cliente_id) if cliente_id else None

        venda = Venda.objects.create(
            loja=loja,
            cliente=cliente,
            forma_pagamento=forma_pagamento,
            desconto=desconto,
            valor_recebido=Decimal(str(valor_recebido)) if valor_recebido else None,
            troco=Decimal(str(troco)) if troco else None,
            criada_por=request.user,
        )

        for item in itens:
            produto = get_object_or_404(Produto, pk=item['produto_id'])
            quantidade = Decimal(str(item['quantidade']))
            preco = Decimal(str(item['preco']))

            ItemVenda.objects.create(
                venda=venda,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=preco,
                subtotal=quantidade * preco,
            )

            estoque, _ = Estoque.objects.get_or_create(
                produto=produto, loja=loja,
                defaults={'quantidade': Decimal('0'), 'estoque_minimo': Decimal('5')}
            )
            estoque.quantidade -= quantidade
            estoque.save()

            MovimentoEstoque.objects.create(
                estoque=estoque,
                tipo='saida',
                quantidade=quantidade,
                observacao=f'Venda #{venda.pk}',
                criado_por=request.user,
            )

        if forma_pagamento == 'fiado' and cliente:
            venc = date.fromisoformat(vencimento_fiado) if vencimento_fiado else date.today() + timedelta(days=30)
            ContaReceber.objects.create(
                venda=venda,
                cliente=cliente,
                descricao=f'Venda #{venda.pk}',
                valor=venda.total,
                vencimento=venc,
            )

        return JsonResponse({'sucesso': True, 'venda_id': venda.pk, 'total': float(venda.total)})

    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
def venda_lista(request):
    vendas = Venda.objects.select_related('cliente', 'criada_por').order_by('-criada_em')[:100]
    return render(request, 'pdv/lista.html', {'vendas': vendas})


@login_required
def venda_detalhe(request, pk):
    venda = get_object_or_404(Venda, pk=pk)
    return render(request, 'pdv/detalhe.html', {'venda': venda})


@login_required
@require_POST
@transaction.atomic
def cancelar_venda(request, pk):
    venda = get_object_or_404(Venda, pk=pk)

    if venda.status == 'cancelada':
        messages.warning(request, 'Esta venda já está cancelada.')
        return redirect('venda_lista')

    # Devolver estoque de cada item
    loja = venda.loja
    for item in venda.itens.all():
        try:
            estoque = Estoque.objects.get(produto=item.produto, loja=loja)
            estoque.quantidade += item.quantidade
            estoque.save()
            MovimentoEstoque.objects.create(
                estoque=estoque,
                tipo='ajuste',
                quantidade=item.quantidade,
                observacao=f'Devolução — Venda #{venda.pk} cancelada',
                criado_por=request.user,
            )
        except Estoque.DoesNotExist:
            pass

    # Cancelar conta a receber se existir
    try:
        venda.conta_receber.delete()
    except:
        pass

    venda.status = 'cancelada'
    venda.save()

    messages.success(request, f'Venda #{venda.pk} cancelada! O estoque foi devolvido automaticamente.')
    return redirect('venda_lista')
