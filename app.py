from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import json
import platform
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

# ─────────────────────────────────────────────────────────────────────────────


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


# ── SMTP FUNCTION ───────────────────────────────────────────────────────────
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


# ── EMAIL HTML ──────────────────────────────────────────────────────────────
def _build_email_html(registros, data_ref, extra_obs=""):
    data_fmt = datetime.strptime(data_ref, '%Y-%m-%d').strftime('%d/%m/%Y')

    linhas = ""
    for r in registros:
        linhas += f"""
        <tr>
            <td>{r['data_br']}</td>
            <td>{r['origem']}</td>
            <td>{r['destino']}</td>
            <td>{r['mp']}</td>
            <td>{r['cod']}</td>
            <td>{r['quantidade']}</td>
            <td>{r['programacao_vol']}</td>
            <td>{r['status']}</td>
        </tr>
        """

    return f"""
    <html>
    <body>
        <h2>Programação - {data_fmt}</h2>
        <table border="1" cellpadding="5">
            <tr>
                <th>Data</th>
                <th>Origem</th>
                <th>Destino</th>
                <th>MP</th>
                <th>Cód</th>
                <th>Qtd</th>
                <th>Volume</th>
                <th>Status</th>
            </tr>
            {linhas}
        </table>
    </body>
    </html>
    """


# ── ROTAS ───────────────────────────────────────────────────────────────────
@app.route('/api/enviar-email', methods=['POST'])
def enviar_email():
    payload = request.json or {}
    data_ref = payload.get('data')
    ids_selecionados = payload.get('ids')

    if not data_ref:
        return jsonify({'success': False, 'error': 'Data não informada'}), 400

    try:
        d = datetime.strptime(data_ref, '%Y-%m-%d').date()
    except:
        return jsonify({'success': False, 'error': 'Data inválida'}), 400

    query = Programacao.query.filter_by(data=d)

    if ids_selecionados:
        query = query.filter(Programacao.id.in_(ids_selecionados))

    registros = query.all()

    if not registros:
        return jsonify({'success': False, 'error': 'Sem dados'}), 404

    registros_dict = [r.to_dict() for r in registros]
    html_body = _build_email_html(registros_dict, data_ref)
    data_fmt = d.strftime('%d/%m/%Y')

    try:
        enviar_email_smtp(html_body, data_fmt)
        return jsonify({'success': True, 'message': 'Email enviado com sucesso!'})

    except smtplib.SMTPAuthenticationError:
        return jsonify({'success': False, 'error': 'Erro de autenticação SMTP'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── INIT DB ────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

# ── RUN ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5050, host='0.0.0.0')

