from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal

from .models import Estoque, MovimentoEstoque
from produtos.models import Produto, Categoria
from lojas.models import Loja


def get_loja():
    return Loja.objects.filter(ativa=True).first()


@login_required
def lista(request):
    loja = get_loja()
    q = request.GET.get('q', '')
    filtro = request.GET.get('filtro', '')

    estoques = Estoque.objects.filter(loja=loja).select_related('produto__categoria').order_by('produto__nome')

    if q:
        estoques = estoques.filter(produto__nome__icontains=q)

    if filtro == 'baixo':
        estoques = [e for e in estoques if e.abaixo_minimo]
    elif filtro == 'zerado':
        estoques = [e for e in estoques if e.quantidade <= 0]
    else:
        estoques = list(estoques)

    # Separar alertas
    alertas = [e for e in estoques if e.abaixo_minimo]

    categorias = Categoria.objects.all().order_by('nome')
    return render(request, 'estoque/lista.html', {
        'estoques': estoques,
        'alertas': alertas,
        'q': q,
        'filtro': filtro,
        'categorias': categorias,
    })


@login_required
def entrada(request, pk):
    estoque = get_object_or_404(Estoque, pk=pk)

    if request.method == 'POST':
        quantidade = request.POST.get('quantidade', '').replace(',', '.')
        observacao = request.POST.get('observacao', '').strip()

        try:
            qtd = Decimal(quantidade)
            if qtd <= 0:
                raise ValueError()
        except:
            messages.error(request, 'Informe uma quantidade válida.')
            return render(request, 'estoque/entrada.html', {'estoque': estoque})

        estoque.quantidade += qtd
        estoque.save()

        MovimentoEstoque.objects.create(
            estoque=estoque,
            tipo='entrada',
            quantidade=qtd,
            observacao=observacao or 'Entrada de mercadoria',
            criado_por=request.user,
        )

        messages.success(request, f'Entrada de {qtd} {estoque.produto.unidade} registrada para "{estoque.produto.nome}"!')
        return redirect('estoque_lista')

    return render(request, 'estoque/entrada.html', {'estoque': estoque})


@login_required
def ajuste(request, pk):
    estoque = get_object_or_404(Estoque, pk=pk)

    if request.method == 'POST':
        nova_qtd = request.POST.get('quantidade', '').replace(',', '.')
        estoque_minimo = request.POST.get('estoque_minimo', '').replace(',', '.')
        observacao = request.POST.get('observacao', '').strip()

        try:
            nova_qtd = Decimal(nova_qtd)
            if nova_qtd < 0:
                raise ValueError()
        except:
            messages.error(request, 'Informe uma quantidade válida.')
            return render(request, 'estoque/ajuste.html', {'estoque': estoque})

        try:
            estoque.estoque_minimo = Decimal(estoque_minimo)
        except:
            pass

        diferenca = nova_qtd - estoque.quantidade
        estoque.quantidade = nova_qtd
        estoque.save()

        MovimentoEstoque.objects.create(
            estoque=estoque,
            tipo='ajuste',
            quantidade=abs(diferenca),
            observacao=observacao or f'Ajuste manual: {nova_qtd} {estoque.produto.unidade}',
            criado_por=request.user,
        )

        messages.success(request, f'Estoque de "{estoque.produto.nome}" ajustado para {nova_qtd} {estoque.produto.unidade}!')
        return redirect('estoque_lista')

    return render(request, 'estoque/ajuste.html', {'estoque': estoque})


@login_required
def historico(request, pk):
    estoque = get_object_or_404(Estoque, pk=pk)
    movimentos = estoque.movimentos.select_related('criado_por').order_by('-criado_em')[:50]
    return render(request, 'estoque/historico.html', {
        'estoque': estoque,
        'movimentos': movimentos,
    })
