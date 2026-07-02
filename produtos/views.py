from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Produto, Categoria


@login_required
def lista(request):
    q = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria', '')

    produtos = Produto.objects.select_related('categoria').order_by('nome')
    if q:
        produtos = produtos.filter(nome__icontains=q) | produtos.filter(codigo__icontains=q)
        produtos = produtos.distinct()
    if categoria_id:
        produtos = produtos.filter(categoria_id=categoria_id)

    categorias = Categoria.objects.all()
    return render(request, 'produtos/lista.html', {
        'produtos': produtos,
        'categorias': categorias,
        'q': q,
        'categoria_id': categoria_id,
    })


@login_required
def novo(request):
    categorias = Categoria.objects.all()
    unidades = Produto.UNIDADE_CHOICES

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        nome = request.POST.get('nome', '').strip()
        categoria_id = request.POST.get('categoria') or None
        unidade = request.POST.get('unidade', 'un')
        preco_custo = request.POST.get('preco_custo', '0').replace(',', '.')
        preco_venda = request.POST.get('preco_venda', '0').replace(',', '.')

        if not codigo or not nome or not preco_venda:
            messages.error(request, 'Preencha código, nome e preço de venda.')
            return render(request, 'produtos/form.html', {'categorias': categorias, 'unidades': unidades})

        if Produto.objects.filter(codigo=codigo).exists():
            messages.error(request, f'Já existe um produto com o código {codigo}.')
            return render(request, 'produtos/form.html', {'categorias': categorias, 'unidades': unidades, 'post': request.POST})

        Produto.objects.create(
            codigo=codigo,
            nome=nome,
            categoria_id=categoria_id,
            unidade=unidade,
            preco_custo=preco_custo,
            preco_venda=preco_venda,
        )
        messages.success(request, f'Produto "{nome}" cadastrado com sucesso!')
        return redirect('produto_lista')

    return render(request, 'produtos/form.html', {'categorias': categorias, 'unidades': unidades})


@login_required
def editar(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    categorias = Categoria.objects.all()
    unidades = Produto.UNIDADE_CHOICES

    if request.method == 'POST':
        produto.codigo = request.POST.get('codigo', '').strip()
        produto.nome = request.POST.get('nome', '').strip()
        produto.categoria_id = request.POST.get('categoria') or None
        produto.unidade = request.POST.get('unidade', 'un')
        produto.preco_custo = request.POST.get('preco_custo', '0').replace(',', '.')
        produto.preco_venda = request.POST.get('preco_venda', '0').replace(',', '.')
        produto.ativo = 'ativo' in request.POST
        produto.save()
        messages.success(request, f'Produto "{produto.nome}" atualizado!')
        return redirect('produto_lista')

    return render(request, 'produtos/form.html', {
        'produto': produto,
        'categorias': categorias,
        'unidades': unidades,
    })


@login_required
@require_POST
def toggle_ativo(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    produto.ativo = not produto.ativo
    produto.save()
    status = 'ativado' if produto.ativo else 'desativado'
    messages.success(request, f'Produto "{produto.nome}" {status} com sucesso!')
    return redirect('produto_lista')


@login_required
@require_POST
def excluir(request, pk):
    from estoque.models import Estoque
    produto = get_object_or_404(Produto, pk=pk)
    nome = produto.nome
    Estoque.objects.filter(produto=produto).delete()
    produto.delete()
    messages.success(request, f'Produto "{nome}" excluido com sucesso!')
    return redirect('estoque_lista')


@login_required
@require_POST
def novo_ajax(request):
    import json
    from django.http import JsonResponse
    from decimal import Decimal
    from lojas.models import Loja
    from estoque.models import Estoque, MovimentoEstoque

    try:
        data = json.loads(request.body)
        codigo = data.get('codigo', '').strip()
        nome = data.get('nome', '').strip()
        preco_venda = data.get('preco_venda', '0')
        estoque_inicial = Decimal(str(data.get('estoque_inicial', 0)))

        if not codigo or not nome or not preco_venda:
            return JsonResponse({'erro': 'Codigo, nome e preco de venda sao obrigatorios.'}, status=400)

        if Produto.objects.filter(codigo=codigo).exists():
            return JsonResponse({'erro': f'Ja existe um produto com o codigo {codigo}.'}, status=400)

        produto = Produto.objects.create(
            codigo=codigo,
            nome=nome,
            categoria_id=data.get('categoria_id') or None,
            unidade=data.get('unidade', 'un'),
            preco_custo=Decimal(str(data.get('preco_custo', 0))),
            preco_venda=Decimal(str(preco_venda)),
        )

        # Criar estoque inicial
        loja = Loja.objects.filter(ativa=True).first()
        if loja:
            est, _ = Estoque.objects.get_or_create(
                produto=produto, loja=loja,
                defaults={'quantidade': estoque_inicial, 'estoque_minimo': 5}
            )
            if estoque_inicial > 0:
                MovimentoEstoque.objects.create(
                    estoque=est,
                    tipo='entrada',
                    quantidade=estoque_inicial,
                    observacao='Estoque inicial no cadastro',
                    criado_por=request.user,
                )

        return JsonResponse({'sucesso': True, 'id': produto.pk, 'nome': produto.nome})
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_POST
def editar_ajax(request, pk):
    import json
    from django.http import JsonResponse
    from decimal import Decimal
    try:
        produto = get_object_or_404(Produto, pk=pk)
        data = json.loads(request.body)
        produto.codigo = data.get('codigo', '').strip()
        produto.nome = data.get('nome', '').strip()
        produto.categoria_id = data.get('categoria_id') or None
        produto.unidade = data.get('unidade', 'un')
        produto.preco_custo = Decimal(str(data.get('preco_custo', 0)))
        produto.preco_venda = Decimal(str(data.get('preco_venda', 0)))
        produto.ativo = data.get('ativo', True)
        produto.save()
        return JsonResponse({'sucesso': True, 'nome': produto.nome})
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_POST
def categoria_ajax(request):
    import json
    from django.http import JsonResponse
    try:
        data = json.loads(request.body)
        nome = data.get('nome', '').strip()
        if not nome:
            return JsonResponse({'erro': 'Nome e obrigatorio.'}, status=400)
        cat, criado = Categoria.objects.get_or_create(nome=nome)
        if not criado:
            return JsonResponse({'erro': f'Categoria "{nome}" ja existe.'}, status=400)
        return JsonResponse({'sucesso': True, 'id': cat.pk, 'nome': cat.nome})
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)
