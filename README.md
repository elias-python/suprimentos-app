# 🌾 Sistema de Programação de Matéria Prima — Suprimentos

Sistema web completo para controle de programações de movimentação de matéria prima de fertilizantes.

## Requisitos

- Python 3.8+
- pip

## Instalação

```bash
# 1. Instalar dependências
pip install flask flask-sqlalchemy

# 2. Rodar o sistema
python app.py
```

## Acesso

Abra no navegador: **http://localhost:5050**

---

## Funcionalidades

### 📊 Dashboard
- KPIs em tempo real: Total, Pendentes, Em Andamento, Confirmados, Urgentes, Volume Total
- Gráficos de barras: Por Tipo de Operação e Por Destino
- Tabela com as programações mais recentes

### 📋 Programações
- Listagem completa com filtros por: Data, Origem, Destino, Status
- Indicador visual de urgência (ponto vermelho pulsante)
- Ações rápidas: visualizar detalhe, editar, excluir
- Contador de registros filtrados

### 🚨 Urgentes
- Painel dedicado apenas às programações marcadas como urgentes
- Acesso rápido para edição e visualização

---

## Campos controlados

| Campo | Descrição |
|-------|-----------|
| Data | Data da operação |
| Origem | Armazém/local de saída do produto |
| Destino | Unidade receptora |
| Produto | Nome completo + código SAP |
| MP (Abrev.) | Abreviação da matéria prima |
| Quantidade | Número de veículos |
| Tipo Veículo | Carreta, Truck, Caminhão Baú, etc. |
| Volume (ton) | Toneladas programadas |
| Período Operação | Janela de horário da operação |
| Horário de Corte | Limite de horário |
| Pedido SAP | Número do pedido |
| Item | Item do pedido |
| Transportadora | Empresa responsável pelo transporte |
| Operação (CFOP) | Retorno, Transferência, Venda, etc. |
| Troca de NF | Sim/Não |
| Status | Pendente / Em andamento / Confirmado / Cancelado |
| Urgente | Flag de urgência |
| Observações | Instruções de descarga, box, etc. |

---

## Estrutura dos Arquivos

```
suprimentos_app/
├── app.py              # Backend Flask + API REST
├── suprimentos.db      # Banco de dados SQLite (gerado automaticamente)
├── templates/
│   └── index.html      # Interface web completa
└── README.md
```

## API REST

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | /api/programacoes | Listar (suporta filtros) |
| POST | /api/programacoes | Criar nova |
| GET | /api/programacoes/:id | Buscar por ID |
| PUT | /api/programacoes/:id | Atualizar |
| DELETE | /api/programacoes/:id | Excluir |
| GET | /api/dashboard | Dados do painel |
| GET | /api/produtos | Lista de produtos |
