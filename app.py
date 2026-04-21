from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy import func

# ── DATABASE ────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///suprimentos.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'suprimentos_secret_2026'
db = SQLAlchemy(app)

# ── SMTP CONFIG ─────────────────────────────────────────────────────────────
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER)

# ── EMAIL DESTINATÁRIOS ─────────────────────────────────────────────────────
EMAIL_DESTINATARIOS = [
    "elias.santana@mosaicco.com",
]

EMAIL_CC = [
    "WILLIAM.SANTANA@mosaicco.com",
]

# ── LISTAS DE OPÇÕES ────────────────────────────────────────────────────────
ORIGENS = [
    "Armazém Central",
    "Porto de Santos",
    "Porto de Paranaguá",
    "Fornecedor A",
    "Fornecedor B",
]

DESTINOS = [
    "Planta Uberaba",
    "Planta Araxá",
    "Planta Catalão",
    "CD Rondonópolis",
    "CD Ponta Grossa",
]

TIPOS_VEICULO = [
    "Bitrem",
    "Rodotrem",
    "Carreta Simples",
    "Treminhão",
    "Graneleiro",
]

TRANSPORTADORAS = [
    "Transportadora Alpha",
    "Logística Beta",
    "Fretes Gamma",
    "Transportes Delta",
    "Cargas Epsilon",
]

OPERACOES = [
    "1.101 — Compra p/ industrialização",
    "1.102 — Compra p/ comercialização",
    "2.101 — Compra p/ industrialização (interstate)",
    "5.101 — Venda de produção",
    "5.102 — Venda de mercadoria adquirida",
    "1.556 — Compra de material para uso e consumo",
]

# Produtos disponíveis (cod, mp, descrição completa)
PRODUTOS = [
    {"cod": "10001", "mp": "MAP",   "produto": "MAP 11-52-00 — Monoamônio Fosfato Granel"},
    {"cod": "10002", "mp": "DAP",   "produto": "DAP 18-46-00 — Diamônio Fosfato Granel"},
    {"cod": "10003", "mp": "MES",   "produto": "MES — Microessential S15 Granel"},
    {"cod": "10004", "mp": "K2O",   "produto": "KCl — Cloreto de Potássio Granel"},
    {"cod": "10005", "mp": "SSP",   "produto": "SSP — Superfosfato Simples Granel"},
    {"cod": "10006", "mp": "TSP",   "produto": "TSP 00-46-00 — Superfosfato Triplo Granel"},
    {"cod": "10007", "mp": "UREA",  "produto": "Ureia 45-00-00 — Granulada Granel"},
    {"cod": "10008", "mp": "AS",    "produto": "Sulfato de Amônio — Granel"},
]


# ── MODEL ───────────────────────────────────────────────────────────────────
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
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow)

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


# ── SMTP ────────────────────────────────────────────────────────────────────
def enviar_email_smtp(html_body, data_fmt):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Mosaic] Programação de MP — {data_fmt}"
    msg["From"] = SMTP_FROM
    msg["To"] = ", ".join(EMAIL_DESTINATARIOS)
    if EMAIL_CC:
        msg["Cc"] = ", ".join(EMAIL_CC)
    msg.attach(MIMEText(html_body, "html"))
    destinatarios = EMAIL_DESTINATARIOS + EMAIL_CC
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_FROM, destinatarios, msg.as_string())


def _build_email_html(registros, data_ref, extra_obs=""):
    data_fmt = datetime.strptime(data_ref, '%Y-%m-%d').strftime('%d/%m/%Y')
    linhas = ""
    for r in registros:
        urg_marker = "🚨 " if r.get('urgente') else ""
        linhas += f"""
        <tr>
            <td>{r['data_br']}</td>
            <td>{r['origem']}</td>
            <td>{r['destino']}</td>
            <td>{urg_marker}{r['mp'] or ''}</td>
            <td>{r['cod'] or ''}</td>
            <td>{r['quantidade'] or ''}</td>
            <td>{r['programacao_vol'] or ''}</td>
            <td>{r['transportadora'] or ''}</td>
            <td>{r['status']}</td>
        </tr>
        """

    obs_block = ""
    if extra_obs:
        obs_block = f"<p><strong>Observação:</strong> {extra_obs}</p>"

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;color:#222">
        <h2 style="color:#006b5e">Programação de MP — {data_fmt}</h2>
        {obs_block}
        <table border="1" cellpadding="6" cellspacing="0"
               style="border-collapse:collapse;width:100%;font-size:13px">
            <thead style="background:#006b5e;color:#fff">
            <tr>
                <th>Data</th><th>Origem</th><th>Destino</th><th>MP</th>
                <th>Cód</th><th>Qtd</th><th>Vol. (t)</th>
                <th>Transportadora</th><th>Status</th>
            </tr>
            </thead>
            <tbody>{linhas}</tbody>
        </table>
        <p style="font-size:11px;color:#888;margin-top:16px">
            Gerado automaticamente pelo sistema Mosaic Supply Chain.
        </p>
    </body>
    </html>
    """


# ── ROTA PRINCIPAL ──────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template(
        'index.html',
        origens=ORIGENS,
        destinos=DESTINOS,
        tipos_veiculo=TIPOS_VEICULO,
        transportadoras=TRANSPORTADORAS,
        operacoes=OPERACOES,
        produtos=PRODUTOS,
        email_destinatarios=EMAIL_DESTINATARIOS,
        email_cc=EMAIL_CC,
    )


# ── API: DASHBOARD ──────────────────────────────────────────────────────────
@app.route('/api/dashboard')
def dashboard():
    hoje = date.today()
    amanha = hoje + timedelta(days=1)

    total        = Programacao.query.count()
    pendentes    = Programacao.query.filter_by(status='Pendente').count()
    em_andamento = Programacao.query.filter_by(status='Em andamento').count()
    confirmados  = Programacao.query.filter_by(status='Confirmado').count()
    urgentes     = Programacao.query.filter_by(urgente=True).count()
    hoje_count   = Programacao.query.filter_by(data=hoje).count()
    amanha_count = Programacao.query.filter_by(data=amanha).count()

    vol_result = db.session.query(func.sum(Programacao.programacao_vol)).scalar()
    volume_total = round(vol_result or 0, 2)

    # Agrupamentos para gráficos
    por_operacao = []
    op_rows = (db.session.query(Programacao.operacao, func.count(Programacao.id))
               .group_by(Programacao.operacao)
               .order_by(func.count(Programacao.id).desc())
               .limit(6).all())
    for operacao, count in op_rows:
        por_operacao.append({'operacao': operacao or 'Sem operação', 'count': count})

    por_destino = []
    dest_rows = (db.session.query(Programacao.destino, func.count(Programacao.id))
                 .group_by(Programacao.destino)
                 .order_by(func.count(Programacao.id).desc())
                 .limit(6).all())
    for destino, count in dest_rows:
        por_destino.append({'destino': destino or '—', 'count': count})

    por_transportadora = []
    transp_rows = (db.session.query(Programacao.transportadora, func.count(Programacao.id))
                   .group_by(Programacao.transportadora)
                   .order_by(func.count(Programacao.id).desc())
                   .limit(6).all())
    for transp, count in transp_rows:
        por_transportadora.append({'transportadora': transp or '—', 'count': count})

    return jsonify({
        'total': total,
        'pendentes': pendentes,
        'em_andamento': em_andamento,
        'confirmados': confirmados,
        'urgentes': urgentes,
        'hoje': hoje_count,
        'amanha': amanha_count,
        'volume_total': volume_total,
        'por_operacao': por_operacao,
        'por_destino': por_destino,
        'por_transportadora': por_transportadora,
    })


# ── API: LISTAR / FILTRAR PROGRAMAÇÕES ──────────────────────────────────────
@app.route('/api/programacoes', methods=['GET'])
def listar_programacoes():
    query = Programacao.query

    data_str  = request.args.get('data')
    origem    = request.args.get('origem')
    destino   = request.args.get('destino')
    status    = request.args.get('status')
    urgente   = request.args.get('urgente')

    if data_str:
        try:
            d = datetime.strptime(data_str, '%Y-%m-%d').date()
            query = query.filter_by(data=d)
        except ValueError:
            return jsonify({'error': 'Data inválida'}), 400

    if origem:
        query = query.filter(Programacao.origem.ilike(f'%{origem}%'))
    if destino:
        query = query.filter(Programacao.destino.ilike(f'%{destino}%'))
    if status:
        query = query.filter_by(status=status)
    if urgente and urgente.lower() == 'true':
        query = query.filter_by(urgente=True)

    rows = query.order_by(Programacao.data.desc(), Programacao.criado_em.desc()).all()
    return jsonify([r.to_dict() for r in rows])


# ── API: BUSCAR UMA PROGRAMAÇÃO ─────────────────────────────────────────────
@app.route('/api/programacoes/<int:id>', methods=['GET'])
def get_programacao(id):
    r = Programacao.query.get_or_404(id)
    return jsonify(r.to_dict())


# ── API: CRIAR PROGRAMAÇÃO ──────────────────────────────────────────────────
@app.route('/api/programacoes', methods=['POST'])
def criar_programacao():
    payload = request.json or {}

    data_str = payload.get('data')
    if not data_str:
        return jsonify({'success': False, 'error': 'Campo "data" obrigatório'}), 400
    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Data inválida'}), 400

    if not payload.get('origem') or not payload.get('destino') or not payload.get('produto'):
        return jsonify({'success': False, 'error': 'Campos obrigatórios: origem, destino, produto'}), 400

    nova = Programacao(
        data=data_obj,
        origem=payload.get('origem'),
        destino=payload.get('destino'),
        cod=payload.get('cod'),
        produto=payload.get('produto'),
        mp=payload.get('mp'),
        periodo_operacao=payload.get('periodo_operacao'),
        horario_corte=payload.get('horario_corte'),
        quantidade=_to_float(payload.get('quantidade')),
        tipo_veiculo=payload.get('tipo_veiculo'),
        programacao_vol=_to_float(payload.get('programacao_vol')),
        pedido=payload.get('pedido'),
        item=payload.get('item'),
        valor_unit=_to_float(payload.get('valor_unit')),
        troca_nf=payload.get('troca_nf', 'Não'),
        operacao=payload.get('operacao'),
        obs=payload.get('obs'),
        transportadora=payload.get('transportadora'),
        urgente=bool(payload.get('urgente', False)),
        status=payload.get('status', 'Pendente'),
    )
    db.session.add(nova)
    db.session.commit()
    return jsonify({'success': True, 'id': nova.id})


# ── API: EDITAR PROGRAMAÇÃO ─────────────────────────────────────────────────
@app.route('/api/programacoes/<int:id>', methods=['PUT'])
def editar_programacao(id):
    r = Programacao.query.get_or_404(id)
    payload = request.json or {}

    data_str = payload.get('data')
    if data_str:
        try:
            r.data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Data inválida'}), 400

    r.origem           = payload.get('origem', r.origem)
    r.destino          = payload.get('destino', r.destino)
    r.cod              = payload.get('cod', r.cod)
    r.produto          = payload.get('produto', r.produto)
    r.mp               = payload.get('mp', r.mp)
    r.periodo_operacao = payload.get('periodo_operacao', r.periodo_operacao)
    r.horario_corte    = payload.get('horario_corte', r.horario_corte)
    r.quantidade       = _to_float(payload.get('quantidade')) if 'quantidade' in payload else r.quantidade
    r.tipo_veiculo     = payload.get('tipo_veiculo', r.tipo_veiculo)
    r.programacao_vol  = _to_float(payload.get('programacao_vol')) if 'programacao_vol' in payload else r.programacao_vol
    r.pedido           = payload.get('pedido', r.pedido)
    r.item             = payload.get('item', r.item)
    r.valor_unit       = _to_float(payload.get('valor_unit')) if 'valor_unit' in payload else r.valor_unit
    r.troca_nf         = payload.get('troca_nf', r.troca_nf)
    r.operacao         = payload.get('operacao', r.operacao)
    r.obs              = payload.get('obs', r.obs)
    r.transportadora   = payload.get('transportadora', r.transportadora)
    r.urgente          = bool(payload.get('urgente', r.urgente))
    r.status           = payload.get('status', r.status)
    r.atualizado_em    = datetime.utcnow()  # atualiza manualmente (fix do bug onupdate)

    db.session.commit()
    return jsonify({'success': True})


# ── API: EXCLUIR PROGRAMAÇÃO ────────────────────────────────────────────────
@app.route('/api/programacoes/<int:id>', methods=['DELETE'])
def deletar_programacao(id):
    r = Programacao.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    return jsonify({'success': True})


# ── API: ENVIAR EMAIL ───────────────────────────────────────────────────────
@app.route('/api/enviar-email', methods=['POST'])
def enviar_email():
    payload = request.json or {}
    data_ref = payload.get('data')
    ids_selecionados = payload.get('ids')
    extra_obs = payload.get('obs', '')

    if not data_ref:
        return jsonify({'success': False, 'error': 'Data não informada'}), 400

    try:
        d = datetime.strptime(data_ref, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Data inválida'}), 400

    query = Programacao.query.filter_by(data=d)
    if ids_selecionados:
        query = query.filter(Programacao.id.in_(ids_selecionados))

    registros = query.all()
    if not registros:
        return jsonify({'success': False, 'error': 'Nenhuma programação encontrada para esta data'}), 404

    registros_dict = [r.to_dict() for r in registros]
    html_body = _build_email_html(registros_dict, data_ref, extra_obs)
    data_fmt = d.strftime('%d/%m/%Y')

    try:
        enviar_email_smtp(html_body, data_fmt)
        return jsonify({'success': True, 'message': f'Email enviado com sucesso para {len(EMAIL_DESTINATARIOS)} destinatário(s)!'})
    except smtplib.SMTPAuthenticationError:
        return jsonify({'success': False, 'error': 'Erro de autenticação SMTP. Verifique as credenciais.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── HELPER ──────────────────────────────────────────────────────────────────
def _to_float(value):
    """Converte valor para float de forma segura, retorna None se inválido."""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# ── INIT DB ─────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()


# ── RUN ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5050, host='0.0.0.0')