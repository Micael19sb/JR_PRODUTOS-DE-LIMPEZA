from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Sum, Count
from decimal import Decimal
from datetime import date
import calendar

from vendas.models import Venda, ItemVenda
from .models import Despesa


def gerar_relatorio_mensal(ano, mes, email_destino):
    """Gera e envia o relatório mensal por email."""

    # Datas do período
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])

    meses = ['Janeiro','Fevereiro','Marco','Abril','Maio','Junho',
             'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
    mes_nome = meses[mes - 1]

    # Vendas do mês
    vendas = Venda.objects.filter(
        status='concluida',
        criada_em__date__gte=primeiro_dia,
        criada_em__date__lte=ultimo_dia,
    )

    total_vendas = sum(v.total for v in vendas)
    qtd_vendas = vendas.count()

    # Por forma de pagamento
    por_pagamento = {}
    for v in vendas:
        forma = v.get_forma_pagamento_display()
        por_pagamento[forma] = por_pagamento.get(forma, Decimal('0')) + v.total

    # Despesas do mês
    despesas = Despesa.objects.filter(data__gte=primeiro_dia, data__lte=ultimo_dia)
    total_despesas = despesas.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    lucro = total_vendas - total_despesas

    # Produtos mais vendidos
    itens = ItemVenda.objects.filter(
        venda__status='concluida',
        venda__criada_em__date__gte=primeiro_dia,
        venda__criada_em__date__lte=ultimo_dia,
    ).values('produto__nome').annotate(
        total_qtd=Sum('quantidade'),
        total_valor=Sum('subtotal')
    ).order_by('-total_qtd')[:5]

    # Montar email HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f8fafc; margin: 0; padding: 20px; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.1); }}
    .header {{ background: #0f172a; padding: 30px; text-align: center; }}
    .header h1 {{ color: #fff; margin: 0; font-size: 22px; }}
    .header p {{ color: #94a3b8; margin: 5px 0 0; font-size: 14px; }}
    .content {{ padding: 24px; }}
    .cards {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
    .card {{ background: #f8fafc; border-radius: 8px; padding: 16px; border: 1px solid #e2e8f0; }}
    .card .label {{ font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; }}
    .card .valor {{ font-size: 22px; font-weight: 700; margin-top: 4px; }}
    .verde {{ color: #15803d; }}
    .vermelho {{ color: #dc2626; }}
    .azul {{ color: #1e40af; }}
    .section {{ margin-bottom: 24px; }}
    .section h2 {{ font-size: 15px; font-weight: 700; color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 12px; }}
    .linha {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
    .footer {{ background: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #94a3b8; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>JR Produtos de Limpeza</h1>
      <p>Relatorio mensal — {mes_nome}/{ano}</p>
    </div>
    <div class="content">

      <div class="cards">
        <div class="card">
          <div class="label">Faturamento bruto</div>
          <div class="valor azul">R$ {total_vendas:,.2f}</div>
        </div>
        <div class="card">
          <div class="label">Total de vendas</div>
          <div class="valor azul">{qtd_vendas} vendas</div>
        </div>
        <div class="card">
          <div class="label">Total despesas</div>
          <div class="valor vermelho">R$ {total_despesas:,.2f}</div>
        </div>
        <div class="card">
          <div class="label">Lucro real</div>
          <div class="valor {'verde' if lucro >= 0 else 'vermelho'}">R$ {lucro:,.2f}</div>
        </div>
      </div>

      <div class="section">
        <h2>Vendas por forma de pagamento</h2>
        {''.join(f'<div class="linha"><span>{forma}</span><span style="font-weight:600">R$ {valor:,.2f}</span></div>' for forma, valor in por_pagamento.items())}
      </div>

      <div class="section">
        <h2>Top 5 produtos mais vendidos</h2>
        {''.join(f'<div class="linha"><span>{item["produto__nome"]}</span><span style="font-weight:600">{item["total_qtd"]} un — R$ {item["total_valor"]:,.2f}</span></div>' for item in itens) if itens else '<p style="color:#64748b;font-size:14px">Nenhum produto vendido no periodo.</p>'}
      </div>

      <div class="section">
        <h2>Despesas do mes</h2>
        {''.join(f'<div class="linha"><span>{d.descricao}</span><span style="font-weight:600;color:#dc2626">R$ {d.valor:,.2f}</span></div>' for d in despesas) if despesas.exists() else '<p style="color:#64748b;font-size:14px">Nenhuma despesa registrada.</p>'}
      </div>

    </div>
    <div class="footer">
      Relatorio gerado automaticamente pelo sistema JR Produtos de Limpeza<br>
      {primeiro_dia.strftime('%d/%m/%Y')} a {ultimo_dia.strftime('%d/%m/%Y')}
    </div>
  </div>
</body>
</html>
"""

    email = EmailMessage(
        subject=f'Relatorio Mensal — {mes_nome}/{ano} | JR Produtos de Limpeza',
        body=html,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email_destino],
    )
    email.content_subtype = 'html'
    email.send()

    return {
        'mes_nome': mes_nome,
        'ano': ano,
        'total_vendas': total_vendas,
        'qtd_vendas': qtd_vendas,
        'total_despesas': total_despesas,
        'lucro': lucro,
    }
