from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import json
import platform

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///suprimentos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'suprimentos_secret_2026'
db = SQLAlchemy(app)

# ── DESTINATÁRIOS DO EMAIL ─────────────────────────────────────────────────────
EMAIL_DESTINATARIOS = [
    "elias.santana@mosaicco.com",
]
# Adicione CC se quiser (pode ser lista vazia)
EMAIL_CC = [
    "WILLIAM.SANTANA@mosaicco.com",
]
# ──────────────────────────────────────────────────────────────────────────────


class Programacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    origem = db.Column(db.String(200), nullable=False)
    destino = db.Column(db.String(200), nullable=False)
    cod = db.Column(db.String(50))
    produto = db.Column(db.String(300), nullable=False)
    mp = db.Column(db.String(100))
    periodo_operacao = db.Column(db.String(100))
    horario_corte = db.Column(db.String(50))
    quantidade = db.Column(db.Float)
    tipo_veiculo = db.Column(db.String(100))
    programacao_vol = db.Column(db.Float)
    pedido = db.Column(db.String(100))
    item = db.Column(db.String(50))
    valor_unit = db.Column(db.Float)
    troca_nf = db.Column(db.String(10), default='Não')
    operacao = db.Column(db.String(200))
    obs = db.Column(db.Text)
    transportadora = db.Column(db.String(200))
    urgente = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='Pendente')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.strftime('%Y-%m-%d') if self.data else None,
            'data_br': self.data.strftime('%d/%m/%Y') if self.data else None,
            'origem': self.origem,
            'destino': self.destino,
            'cod': self.cod,
            'produto': self.produto,
            'mp': self.mp,
            'periodo_operacao': self.periodo_operacao,
            'horario_corte': self.horario_corte,
            'quantidade': self.quantidade,
            'tipo_veiculo': self.tipo_veiculo,
            'programacao_vol': self.programacao_vol,
            'pedido': self.pedido,
            'item': self.item,
            'valor_unit': self.valor_unit,
            'troca_nf': self.troca_nf,
            'operacao': self.operacao,
            'obs': self.obs,
            'transportadora': self.transportadora,
            'urgente': self.urgente,
            'status': self.status,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M') if self.criado_em else None,
        }


# ── DADOS DE REFERÊNCIA ────────────────────────────────────────────────────────
ORIGENS = [
    'Az. Multitrans Matriz', 'Az. Multitrans 3', 'Az. Fortesolo',
    'Az. Rocha Fidelidade', 'Az. Rocha Margarida', 'Az. Rocha Praça',
    'Az. Rocha Brascargo', 'Az. Fertiservice 1', 'Az. Fertiservice 2',
    'Az. Sulmare', 'Az. Faz', 'Az. AEC33', 'Fábrica Fospar',
    'Toll Coonagro', 'Cais Comercial', 'Terminal Fospar'
]

DESTINOS = [
    'Mosaic 1', 'Mosaic 2', 'Az. Multitrans Matriz', 'Az. Multitrans 3',
    'Az. Fortesolo', 'Az. Rocha Fidelidade', 'Az. Rocha Margarida',
    'Az. Rocha Praça', 'Az. Fertiservice 1', 'Az. Fertiservice 2',
    'Fábrica Fospar', 'Toll Coonagro'
]

OPERACOES = [
    'Retorno de armazenagem', 'Transferência', 'Entrada direta',
    'Venda', 'Devolução', 'Remessa para industrialização',
    'Remessa de retorno de industrialização'
]

TRANSPORTADORAS = [
    'Copadubo', 'Tico Transportes', 'Logic', 'TransBrasil',
    'Rodoviário Sul', 'Agrocargo', 'Fertrans'
]

TIPOS_VEICULO = ['Carreta', 'Truck', 'Caminhão Bau', 'Caminhão Toco', 'Bitrem']

PRODUTOS = [
    {'cod': '1013831', 'produto': 'MP - S9 10 46 00 - MICROESSENTIALS GR', 'mp': 'S9 10 46'},
    {'cod': '8000279', 'produto': 'ETF11', 'mp': 'ETF11'},
    {'cod': '8000396', 'produto': 'ETF12', 'mp': 'ETF12'},
    {'cod': '1019856', 'produto': 'MP - SSGR 18,5/16P2O5+21CA+11S GR', 'mp': 'SSP 18,5'},
    {'cod': '1000192', 'produto': 'MP - FOSF.MON.MAP 11N 52/44P2O5 GR', 'mp': 'MAP 11 52'},
    {'cod': '1002950', 'produto': 'MP - CLORETO DE POTASSIO 60K2O GRANULADO', 'mp': 'KCL 60'},
    {'cod': '1016792', 'produto': 'MP - UREIA 46 N GRANULADA', 'mp': 'Ureia'},
    {'cod': '1002991', 'produto': 'MP - SULFATO DE AMONIO 21N 24S GR', 'mp': 'SAM 21'},
    {'cod': '1000199', 'produto': 'MP - SUPERF.TRIPLO 46/36 P2O5 +10 CA GR', 'mp': 'TSP 46'},
    {'cod': '1003024', 'produto': 'MP - SUPERF.TRIPLO 45/36 P2O5+10 CA GR', 'mp': 'TSP 45'},
    {'cod': '1003095', 'produto': 'MP - BORO 10B GR', 'mp': 'Boro 10'},
    {'cod': '1016785', 'produto': 'MP - BORO 4B GR', 'mp': 'Boro 4'},
    {'cod': '1017930', 'produto': 'MP - KMAG 21,5K2O 21S 10,5MG GR', 'mp': 'KMAG'},
    {'cod': '1002935', 'produto': 'MP - FOSF.MON.MAP 10N 50/44P2O5 GR', 'mp': 'MAP 10 50'},
    {'cod': '1003080', 'produto': 'MP - FOSF.MON.MAP 12N 52/48P2O5 GR', 'mp': 'MAP 12'},
    {'cod': '1018337', 'produto': 'MP - SSGR 20/17P2O5 + 16CA + 10S IMP GR', 'mp': 'SSP 20'},
    {'cod': '1017209', 'produto': 'MP - ASPIRE 00 00 58 + 0,5 B GR', 'mp': 'Aspire'},
    {'cod': '1021388', 'produto': 'MP - 00 43 00', 'mp': 'TSP 43'},
    {'cod': '1003136', 'produto': 'MP - 02 18 00 + 200 KG FMA BR 132 GR', 'mp': '02 18'},
    {'cod': '1002948', 'produto': 'MP - S15 13 33 00 - MICROESSENTIALS GR', 'mp': 'S15 13 33'},
]


def seed_data():
    if Programacao.query.count() == 0:
        from datetime import timedelta
        amanha = date.today() + timedelta(days=1)
        registros = [
            Programacao(
                data=amanha,
                origem='Az. Multitrans Matriz', destino='Mosaic 1',
                cod='1013831', produto='MP - S9 10 46 00 - MICROESSENTIALS GR', mp='S9 10 46',
                periodo_operacao='07:00 as 15:00', horario_corte='16:00',
                quantidade=8, tipo_veiculo='Carreta', programacao_vol=450,
                pedido='4530027786', item='20', troca_nf='Não',
                operacao='Retorno de armazenagem', obs='Moega Box 12',
                transportadora='Copadubo', urgente=False, status='Pendente'
            ),
            Programacao(
                data=amanha,
                origem='Az. Fortesolo', destino='Mosaic 2',
                cod='1019856', produto='MP - SSGR 18,5/16P2O5+21CA+11S GR', mp='SSP 18,5',
                periodo_operacao='08:00 as 17:00', horario_corte='15:30',
                quantidade=4, tipo_veiculo='Truck', programacao_vol=200,
                pedido='4530028422', item='20', troca_nf='Não',
                operacao='Retorno de armazenagem', obs='Descarga por baixo Box 02',
                transportadora='Logic', urgente=True, status='Pendente'
            ),
            Programacao(
                data=date.today(),
                origem='Fábrica Fospar', destino='Mosaic 2',
                cod='1019856', produto='MP - SSGR 18,5/16P2O5+21CA+11S GR', mp='SSP 18,5',
                periodo_operacao='08:00 as 17:00', horario_corte='15:30',
                quantidade=4, tipo_veiculo='Truck', programacao_vol=200,
                pedido='4530034707', item='10', troca_nf='Não',
                operacao='Transferência', obs='Descarga por baixo Box 02',
                transportadora='Logic', urgente=False, status='Em andamento'
            ),
        ]
        for r in registros:
            db.session.add(r)
        db.session.commit()


# ── ROTAS PRINCIPAIS ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html',
        origens=ORIGENS, destinos=DESTINOS, operacoes=OPERACOES,
        transportadoras=TRANSPORTADORAS, tipos_veiculo=TIPOS_VEICULO,
        produtos=PRODUTOS,
        email_destinatarios=EMAIL_DESTINATARIOS,
        email_cc=EMAIL_CC)


@app.route('/api/programacoes', methods=['GET'])
def get_programacoes():
    data_filtro = request.args.get('data')
    origem_filtro = request.args.get('origem')
    destino_filtro = request.args.get('destino')
    status_filtro = request.args.get('status')
    urgente_filtro = request.args.get('urgente')

    query = Programacao.query
    if data_filtro:
        try:
            d = datetime.strptime(data_filtro, '%Y-%m-%d').date()
            query = query.filter(Programacao.data == d)
        except Exception:
            pass
    if origem_filtro:
        query = query.filter(Programacao.origem.ilike(f'%{origem_filtro}%'))
    if destino_filtro:
        query = query.filter(Programacao.destino.ilike(f'%{destino_filtro}%'))
    if status_filtro:
        query = query.filter(Programacao.status == status_filtro)
    if urgente_filtro == 'true':
        query = query.filter(Programacao.urgente == True)

    registros = query.order_by(Programacao.data.asc(), Programacao.id.asc()).all()
    return jsonify([r.to_dict() for r in registros])


@app.route('/api/programacoes', methods=['POST'])
def criar_programacao():
    data = request.json
    try:
        p = Programacao(
            data=datetime.strptime(data['data'], '%Y-%m-%d').date(),
            origem=data['origem'],
            destino=data['destino'],
            cod=data.get('cod'),
            produto=data['produto'],
            mp=data.get('mp'),
            periodo_operacao=data.get('periodo_operacao'),
            horario_corte=data.get('horario_corte'),
            quantidade=float(data['quantidade']) if data.get('quantidade') else None,
            tipo_veiculo=data.get('tipo_veiculo'),
            programacao_vol=float(data['programacao_vol']) if data.get('programacao_vol') else None,
            pedido=data.get('pedido'),
            item=data.get('item'),
            valor_unit=float(data['valor_unit']) if data.get('valor_unit') else None,
            troca_nf=data.get('troca_nf', 'Não'),
            operacao=data.get('operacao'),
            obs=data.get('obs'),
            transportadora=data.get('transportadora'),
            urgente=data.get('urgente', False),
            status=data.get('status', 'Pendente'),
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({'success': True, 'id': p.id, 'data': p.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/programacoes/<int:id>', methods=['PUT'])
def atualizar_programacao(id):
    p = Programacao.query.get_or_404(id)
    data = request.json
    try:
        if 'data' in data:
            p.data = datetime.strptime(data['data'], '%Y-%m-%d').date()
        for campo in ['origem', 'destino', 'cod', 'produto', 'mp', 'periodo_operacao',
                      'horario_corte', 'tipo_veiculo', 'pedido', 'item', 'troca_nf',
                      'operacao', 'obs', 'transportadora', 'status']:
            if campo in data:
                setattr(p, campo, data[campo])
        for campo_num in ['quantidade', 'programacao_vol', 'valor_unit']:
            if campo_num in data:
                setattr(p, campo_num, float(data[campo_num]) if data[campo_num] else None)
        if 'urgente' in data:
            p.urgente = bool(data['urgente'])
        p.atualizado_em = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'data': p.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/programacoes/<int:id>', methods=['DELETE'])
def deletar_programacao(id):
    p = Programacao.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/programacoes/<int:id>', methods=['GET'])
def get_programacao(id):
    p = Programacao.query.get_or_404(id)
    return jsonify(p.to_dict())


@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    from sqlalchemy import func
    total = Programacao.query.count()
    pendentes = Programacao.query.filter_by(status='Pendente').count()
    em_andamento = Programacao.query.filter_by(status='Em andamento').count()
    confirmados = Programacao.query.filter_by(status='Confirmado').count()
    urgentes = Programacao.query.filter_by(urgente=True).count()
    hoje = date.today()
    hoje_count = Programacao.query.filter_by(data=hoje).count()

    from datetime import timedelta
    amanha = hoje + timedelta(days=1)
    amanha_count = Programacao.query.filter_by(data=amanha).count()

    vol = db.session.query(func.sum(Programacao.programacao_vol)).scalar() or 0

    op_counts = db.session.query(
        Programacao.operacao, func.count(Programacao.id)
    ).group_by(Programacao.operacao).all()

    dest_counts = db.session.query(
        Programacao.destino, func.count(Programacao.id)
    ).group_by(Programacao.destino).order_by(func.count(Programacao.id).desc()).limit(5).all()

    transp_counts = db.session.query(
        Programacao.transportadora, func.count(Programacao.id)
    ).group_by(Programacao.transportadora).order_by(func.count(Programacao.id).desc()).limit(5).all()

    return jsonify({
        'total': total,
        'pendentes': pendentes,
        'em_andamento': em_andamento,
        'confirmados': confirmados,
        'urgentes': urgentes,
        'hoje': hoje_count,
        'amanha': amanha_count,
        'volume_total': round(vol, 1),
        'por_operacao': [{'operacao': o, 'count': c} for o, c in op_counts if o],
        'por_destino': [{'destino': d, 'count': c} for d, c in dest_counts if d],
        'por_transportadora': [{'transportadora': t, 'count': c} for t, c in transp_counts if t],
    })


@app.route('/api/produtos', methods=['GET'])
def get_produtos():
    return jsonify(PRODUTOS)


# ── EMAIL VIA OUTLOOK ──────────────────────────────────────────────────────────
def _build_email_html(registros, data_ref, extra_obs=""):
    """Monta o corpo HTML do email com a tabela de programações."""
    data_fmt = datetime.strptime(data_ref, '%Y-%m-%d').strftime('%d/%m/%Y') if data_ref else "—"

    urgentes = [r for r in registros if r.get('urgente')]
    alerta_urg = ""
    if urgentes:
        nomes = ", ".join(r.get('mp') or r.get('produto','')[:20] for r in urgentes)
        alerta_urg = f"""
        <tr><td colspan="10" style="background:#7f1d1d;color:#fca5a5;padding:10px 14px;
            font-weight:700;font-size:13px;">
            🚨 ATENÇÃO — Itens URGENTES: {nomes}
        </td></tr>"""

    linhas = ""
    for i, r in enumerate(registros):
        bg = "#1a2230" if i % 2 == 0 else "#1e2940"
        urg_style = "border-left:3px solid #ef4444;" if r.get('urgente') else ""
        status_colors = {
            'Pendente': '#f59e0b', 'Em andamento': '#3b82f6',
            'Confirmado': '#22c55e', 'Cancelado': '#ef4444'
        }
        sc = status_colors.get(r.get('status',''), '#9ca3af')
        linhas += f"""
        <tr style="background:{bg};{urg_style}">
          <td style="padding:9px 10px;white-space:nowrap;font-size:12px;">{r.get('data_br','')}</td>
          <td style="padding:9px 10px;font-size:12px;">{r.get('origem','')}</td>
          <td style="padding:9px 10px;font-size:12px;font-weight:600;">{r.get('destino','')}</td>
          <td style="padding:9px 10px;font-size:11px;font-family:monospace;">{r.get('mp','')}</td>
          <td style="padding:9px 10px;font-size:11px;font-family:monospace;">{r.get('cod','')}</td>
          <td style="padding:9px 10px;font-size:12px;text-align:center;">{int(r['quantidade']) if r.get('quantidade') else '—'} × {r.get('tipo_veiculo','')}</td>
          <td style="padding:9px 10px;font-size:12px;text-align:right;font-family:monospace;">{r.get('programacao_vol','—')} t</td>
          <td style="padding:9px 10px;font-size:11px;">{r.get('pedido','—')}/{r.get('item','')}</td>
          <td style="padding:9px 10px;font-size:11px;">{r.get('operacao','—')}</td>
          <td style="padding:9px 10px;font-size:11px;color:{sc};font-weight:700;">{r.get('status','')}</td>
        </tr>"""
        if r.get('obs'):
            linhas += f"""
        <tr style="background:{bg};">
          <td colspan="10" style="padding:4px 10px 10px 24px;font-size:11px;color:#9ca3af;font-style:italic;">
            📝 {r.get('obs','')}
          </td>
        </tr>"""

    vol_total = sum(r.get('programacao_vol') or 0 for r in registros)
    qtd_total = sum(int(r.get('quantidade') or 0) for r in registros)
    obs_rodape = f"<p style='margin:12px 0 0;font-size:12px;color:#9ca3af;'>📋 {extra_obs}</p>" if extra_obs else ""

    return f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0d1117;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:900px;margin:24px auto;background:#161b27;border-radius:12px;
    overflow:hidden;border:1px solid #2a3441;">

  <!-- HEADER -->
  <div style="background:linear-gradient(135deg,#00544D,#007a6e);padding:24px 28px;">
    <div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.5px;">
      🌱 Mosaic Supply Chain
    </div>
    <div style="font-size:14px;color:#a7f3d0;margin-top:4px;font-weight:500;">
      Programação de Matérias-Primas — {data_fmt}
    </div>
  </div>

  <!-- RESUMO -->
  <div style="padding:20px 28px;background:#1a2230;border-bottom:1px solid #2a3441;
      display:flex;gap:32px;flex-wrap:wrap;">
    <div>
      <div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#6b7280;text-transform:uppercase;">Total Viagens</div>
      <div style="font-size:28px;font-weight:800;color:#fff;font-family:monospace;">{qtd_total}</div>
    </div>
    <div>
      <div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#6b7280;text-transform:uppercase;">Volume Total</div>
      <div style="font-size:28px;font-weight:800;color:#00d4aa;font-family:monospace;">{vol_total:,.0f} t</div>
    </div>
    <div>
      <div style="font-size:10px;font-weight:700;letter-spacing:1px;color:#6b7280;text-transform:uppercase;">Programações</div>
      <div style="font-size:28px;font-weight:800;color:#fff;font-family:monospace;">{len(registros)}</div>
    </div>
    {"<div><div style='font-size:10px;font-weight:700;letter-spacing:1px;color:#ef4444;text-transform:uppercase;'>⚠ Urgentes</div><div style='font-size:28px;font-weight:800;color:#ef4444;font-family:monospace;'>" + str(len(urgentes)) + "</div></div>" if urgentes else ""}
  </div>

  <!-- TABELA -->
  <div style="padding:20px 28px;">
    <table style="width:100%;border-collapse:collapse;font-size:12px;color:#d1d5db;">
      <thead>
        <tr style="background:#0d1117;">
          <th style="padding:10px;text-align:left;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#6b7280;border-bottom:1px solid #2a3441;">Data</th>
          <th style="padding:10px;text-align:left;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#6b7280;border-bottom:1px solid #2a3441;">Origem</th>
          <th style="padding:10px;text-align:left;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#6b7280;border-bottom:1px solid #2a3441;">Destino</th>
          <th style="padding:10px;text-align:left;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#6b7280;border-bottom:1px solid #2a3441;">MP</th>
          <th style="padding:10px;text-align:left;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#6b7280;border-bottom:1px solid #2a3441;">Cód.</th>
          <th style="padding:10px;text-align:left;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#6b7280;border-bottom:1px solid #2a3441;">Qtd/Veículo</th>
          <th style="padding:10px;text-align:right;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#6b7280;border-bottom:1px solid #2a3441;">Vol.</th>
          <th style="padding:10px;text-align:left;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#6b7280;border-bottom:1px solid #2a3441;">Pedido/Item</th>
          <th style="padding:10px;text-align:left;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#6b7280;border-bottom:1px solid #2a3441;">Operação</th>
          <th style="padding:10px;text-align:left;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#6b7280;border-bottom:1px solid #2a3441;">Status</th>
        </tr>
        {alerta_urg}
      </thead>
      <tbody>{linhas}</tbody>
    </table>
  </div>

  <!-- RODAPÉ -->
  <div style="padding:16px 28px 24px;border-top:1px solid #2a3441;">
    <p style="margin:0;font-size:11px;color:#6b7280;">
      Enviado automaticamente pelo sistema Mosaic Supply Chain em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.
      Não responda este email diretamente.
    </p>
    {obs_rodape}
  </div>

</div>
</body></html>"""


@app.route('/api/enviar-email', methods=['POST'])
def enviar_email():
    """Envia programação via Outlook (win32com). Só funciona em Windows com Outlook instalado."""
    payload = request.json or {}
    data_ref = payload.get('data')          # 'YYYY-MM-DD'
    extra_obs = payload.get('obs', '')       # observação extra opcional
    ids_selecionados = payload.get('ids')    # lista de IDs ou None (todos da data)

    if not data_ref:
        return jsonify({'success': False, 'error': 'Data não informada'}), 400

    # Busca registros
    try:
        d = datetime.strptime(data_ref, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'success': False, 'error': 'Data inválida'}), 400

    query = Programacao.query.filter_by(data=d)
    if ids_selecionados:
        query = query.filter(Programacao.id.in_(ids_selecionados))
    registros = query.order_by(Programacao.origem, Programacao.id).all()

    if not registros:
        return jsonify({'success': False, 'error': 'Nenhuma programação encontrada para esta data'}), 404

    registros_dict = [r.to_dict() for r in registros]
    data_fmt = d.strftime('%d/%m/%Y')
    html_body = _build_email_html(registros_dict, data_ref, extra_obs)

    # Detecta SO
    if platform.system() != 'Windows':
        return jsonify({
            'success': False,
            'error': 'Envio de email via Outlook só está disponível no Windows. '
                     'No Linux/Mac, configure SMTP em app.py (seção alternativa).'
        }), 400

    try:
        import win32com.client
        outlook = win32com.client.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.Subject = f'[Mosaic] Programação de MP — {data_fmt}'
        mail.HTMLBody = html_body
        mail.To = '; '.join(EMAIL_DESTINATARIOS)
        if EMAIL_CC:
            mail.CC = '; '.join(EMAIL_CC)
        mail.Send()
        return jsonify({'success': True, 'message': f'Email enviado para {len(EMAIL_DESTINATARIOS)} destinatário(s)!'})
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Biblioteca win32com não instalada. Execute: pip install pywin32'
        }), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro ao enviar email: {str(e)}'}), 500


# ── ALTERNATIVA SMTP (para Linux/Mac ou sem Outlook) ──────────────────────────
# Se quiser usar SMTP em vez de Outlook, descomente e configure:
#
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
#
# SMTP_HOST = 'smtp.empresa.com.br'
# SMTP_PORT = 587
# SMTP_USER = 'sistema@empresa.com.br'
# SMTP_PASS = 'sua_senha'
#
# def enviar_via_smtp(html_body, data_fmt):
#     msg = MIMEMultipart('alternative')
#     msg['Subject'] = f'[Mosaic] Programação de MP — {data_fmt}'
#     msg['From'] = SMTP_USER
#     msg['To'] = ', '.join(EMAIL_DESTINATARIOS)
#     msg.attach(MIMEText(html_body, 'html'))
#     with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
#         server.starttls()
#         server.login(SMTP_USER, SMTP_PASS)
#         server.sendmail(SMTP_USER, EMAIL_DESTINATARIOS, msg.as_string())
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True, port=5050, host='0.0.0.0')