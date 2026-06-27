# LimpaVendas — Sistema de Gestão de Vendas

Sistema web desenvolvido em Django para gerenciar vendas, estoque e financeiro de empresa de produtos de limpeza com múltiplas filiais.

---

## Instalação rápida

### 1. Pré-requisitos
- Python 3.10+
- pip

### 2. Configurar ambiente

```bash
# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar o banco de dados

```bash
python manage.py makemigrations lojas produtos vendas estoque clientes financeiro relatorios
python manage.py migrate
```

### 4. Popular dados iniciais

```bash
python manage.py shell < setup_inicial.py
```

### 5. Rodar o servidor

```bash
python manage.py runserver
```

Acesse: **http://localhost:8000**

---

## Usuários criados pelo setup

| Usuário | Senha | Acesso |
|---|---|---|
| `dono` | `dono123` | Todas as lojas |
| `vendedor_for` | `vend123` | Loja Fortaleza |
| `vendedor_nat` | `vend123` | Loja Natal |

> **Importante:** Troque as senhas em produção!

---

## Estrutura do projeto

```
vendas_limpeza/
├── core/           # Configurações Django
├── lojas/          # Lojas e perfis de usuário
├── produtos/       # Catálogo de produtos
├── vendas/         # PDV e registro de vendas
├── estoque/        # Controle de estoque por loja
├── clientes/       # Cadastro de clientes
├── financeiro/     # Contas a receber / fiado
├── relatorios/     # Dashboard e relatórios
├── templates/      # HTML das telas
├── static/         # CSS e JS
├── setup_inicial.py
└── requirements.txt
```

---

## Funcionalidades

- **PDV (Ponto de Venda):** registro de vendas com busca de produto, múltiplas formas de pagamento (dinheiro, PIX, cartão, fiado)
- **Estoque:** controle por loja, alertas de estoque mínimo, movimentos de entrada/saída
- **Clientes:** cadastro por loja, histórico de compras
- **Financeiro:** controle de contas a receber, controle de fiado com vencimento
- **Dashboard:** visão consolidada do dia, mês, alertas e comparativo entre lojas
- **Multi-loja:** cada vendedor acessa apenas sua loja; o dono vê tudo

---

## Deploy em produção (Railway/Render)

1. Crie um arquivo `.env`:
```
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=seudominio.com
```

2. Troque SQLite por PostgreSQL no `settings.py` alterando `DATABASES`.

3. Rode `python manage.py collectstatic` antes do deploy.
