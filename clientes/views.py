from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Cliente
from lojas.models import Loja


def get_loja():
    return Loja.objects.filter(ativa=True).first()


@login_required
def lista(request):
    q = request.GET.get('q', '')
    clientes = Cliente.objects.order_by('nome')
    if q:
        clientes = clientes.filter(nome__icontains=q)
    return render(request, 'clientes/lista.html', {'clientes': clientes, 'q': q})


@login_required
def novo(request):
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        cpf_cnpj = request.POST.get('cpf_cnpj', '').strip()
        endereco = request.POST.get('endereco', '').strip()

        if not nome:
            messages.error(request, 'O nome do cliente é obrigatório.')
            return render(request, 'clientes/form.html', {'post': request.POST})

        Cliente.objects.create(
            nome=nome,
            telefone=telefone,
            cpf_cnpj=cpf_cnpj,
            endereco=endereco,
            loja=get_loja(),
        )
        messages.success(request, f'Cliente "{nome}" cadastrado com sucesso!')
        return redirect('cliente_lista')

    return render(request, 'clientes/form.html', {})


@login_required
def editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        cliente.nome = request.POST.get('nome', '').strip()
        cliente.telefone = request.POST.get('telefone', '').strip()
        cliente.cpf_cnpj = request.POST.get('cpf_cnpj', '').strip()
        cliente.endereco = request.POST.get('endereco', '').strip()
        cliente.ativo = 'ativo' in request.POST
        cliente.save()
        messages.success(request, f'Cliente "{cliente.nome}" atualizado!')
        return redirect('cliente_lista')

    return render(request, 'clientes/form.html', {'cliente': cliente})


@login_required
def detalhe(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    vendas = cliente.vendas.order_by('-criada_em')[:20]
    contas = cliente.contas.order_by('vencimento')
    contas_pendentes = [c for c in contas if not c.pago]
    total_devido = sum(c.valor for c in contas_pendentes)
    return render(request, 'clientes/detalhe.html', {
        'cliente': cliente,
        'vendas': vendas,
        'contas': contas,
        'contas_pendentes': contas_pendentes,
        'total_devido': total_devido,
    })


@login_required
@require_POST
def novo_ajax(request):
    import json
    from django.http import JsonResponse
    try:
        data = json.loads(request.body)
        nome = data.get('nome', '').strip()
        if not nome:
            return JsonResponse({'erro': 'Nome é obrigatório.'}, status=400)

        cliente = Cliente.objects.create(
            nome=nome,
            telefone=data.get('telefone', '').strip(),
            cpf_cnpj=data.get('cpf_cnpj', '').strip(),
            endereco=data.get('endereco', '').strip(),
            loja=get_loja(),
        )
        return JsonResponse({'sucesso': True, 'id': cliente.pk, 'nome': cliente.nome})
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


@login_required
@require_POST
def excluir(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    nome = cliente.nome
    cliente.delete()
    messages.success(request, f'Cliente "{nome}" excluído com sucesso!')
    return redirect('cliente_lista')


@login_required
@require_POST
def quitar_tudo(request, pk):
    from datetime import date
    cliente = get_object_or_404(Cliente, pk=pk)
    contas = cliente.contas.filter(pago=False)
    for conta in contas:
        conta.pago = True
        conta.data_pagamento = date.today()
        conta.save()
    messages.success(request, f'Toda a divida de "{cliente.nome}" foi quitada!')
    return redirect('cliente_detalhe', pk=pk)
