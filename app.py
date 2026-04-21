from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
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

# ── SMTP ────────────────────────────────────────────────────────────────────
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER)

EMAIL_DESTINATARIOS = ["elias.santana@mosaicco.com"]
EMAIL_CC            = ["WILLIAM.SANTANA@mosaicco.com"]

# ── LISTAS REAIS (extraídas da planilha de Abril/2026) ──────────────────────
ORIGENS = [
    "Az. Fortesolo",
    "Az. Multitrans 3",
    "Az. Multitrans Matriz",
    "Fábrica Fospar",
]

DESTINOS = [
    "Mosaic 1",
    "Mosaic 2",
]

TIPOS_VEICULO = [
    "Caminhão Bau",
    "Carreta",
    "Truck",
]

TRANSPORTADORAS = [
    "Copadubo",
    "Logic",
    "Tico Transportes",
]

OPERACOES = [
    "Retorno de armazenagem",
    "Transferência",
    "Remessa para Industrialização",
    "Retorno de Industrialização",
    "Compra p/ industrialização (1.101)",
    "Compra p/ comercialização (1.102)",
    "Venda de produção (5.101)",
]

# 203 produtos reais da aba BD
PRODUTOS = [
  {"cod": "1000176", "produto": "MP - FOSFATO DIAMONIO 18N 46/40P2O5 GR", "mp": "DAP"},
  {"cod": "1000191", "produto": "MP - FOSF.MON.MAP FAR.10N 49/44 P2O5", "mp": ""},
  {"cod": "1000192", "produto": "MP - FOSF.MON.MAP 11N 52/44P2O5 GR", "mp": "MAP 11 52"},
  {"cod": "1000194", "produto": "MP - KMAG GR  22K 22S 10MG -GRANUL", "mp": ""},
  {"cod": "1000197", "produto": "MP - UREIA 45 N", "mp": ""},
  {"cod": "1000199", "produto": "MP - SUPERF.TRIPLO 46/36 P2O5 +10 CA GR", "mp": "TSP 46"},
  {"cod": "1000201", "produto": "MP - KMAG GR 21K2O KMAG PREMIUM", "mp": ""},
  {"cod": "1000215", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1001764", "produto": "MP - BIOFOS - FOSFATO MONOCALCICO", "mp": ""},
  {"cod": "1002935", "produto": "MP - FOSF.MON.MAP 10N 50/44P2O5 GR", "mp": "MAP 10 50"},
  {"cod": "1002948", "produto": "MP - S15 13 33 00 - MICROESSENTIALS GR", "mp": "S15 13 33"},
  {"cod": "1002950", "produto": "MP - CLORETO DE POTASSIO 60K2O GRANULADO", "mp": "KCL 60"},
  {"cod": "1002990", "produto": "MP - SULFATO DE AMONIO GR 20N 23S", "mp": ""},
  {"cod": "1002991", "produto": "MP - SULFATO DE AMONIO 21N 24S GR", "mp": "SAM 21"},
  {"cod": "1002993", "produto": "MP - SULFATO DE AMONIO FAR. 21N 24S", "mp": "SAM Fr"},
  {"cod": "1002995", "produto": "MP - UREIA  45 N GRANULADA", "mp": ""},
  {"cod": "1002997", "produto": "MP - UREIA  46 N  PREMIUM (STD)", "mp": ""},
  {"cod": "1002998", "produto": "MP - NITRATO DE AMONIO 34 N", "mp": ""},
  {"cod": "1003012", "produto": "MP - SSGR 20/18P2O5+ 19CA + 11S", "mp": ""},
  {"cod": "1003015", "produto": "MP - SSPO 18/15P2O5+17CA+10S", "mp": ""},
  {"cod": "1003020", "produto": "MP - SSGR 18/15P2O5 + 16CA+8S", "mp": ""},
  {"cod": "1003021", "produto": "MP - SSGR 19/16P2O5+21CA+11S GR", "mp": ""},
  {"cod": "1003024", "produto": "MP - SUPERF.TRIPLO 45/36 P2O5+10 CA GR", "mp": "TSP 45"},
  {"cod": "1003025", "produto": "MP - SUPERF.TRIPLO GR 45/37 P2O5 + 10 CA", "mp": ""},
  {"cod": "1003026", "produto": "MP - SUPERF.TRIPLO GR 42/36 P2O5 + 10CA", "mp": ""},
  {"cod": "1003028", "produto": "MP - SSGR 21/15P2O5+ 18CA + 10S", "mp": ""},
  {"cod": "1003048", "produto": "MP - CLORETO DE POTASSIO 60K2O FARELADO", "mp": "KCL Fr"},
  {"cod": "1003049", "produto": "MP - CLORETO DE POTASSIO 58K2O GRANULADO", "mp": ""},
  {"cod": "1003066", "produto": "MP - FOSF.MON.MAP FAR.11N 52/47P2O5", "mp": ""},
  {"cod": "1003077", "produto": "MP - FOSF.MON.MAP FR 10N 50/44P2O5", "mp": ""},
  {"cod": "1003080", "produto": "MP - FOSF.MON.MAP  12N 52/48P2O5 GR", "mp": "MAP 12"},
  {"cod": "1003081", "produto": "MP - 20 20 00 GR", "mp": ""},
  {"cod": "1003089", "produto": "MP - VARREDURA", "mp": "Varredura"},
  {"cod": "1003095", "produto": "MP - BORO  10B GR", "mp": "Boro 10"},
  {"cod": "1003098", "produto": "MP - ZINCO GR 20", "mp": ""},
  {"cod": "1003101", "produto": "MP - ZINCO  10 GR", "mp": ""},
  {"cod": "1003105", "produto": "MP - ZINCO GR 15", "mp": ""},
  {"cod": "1003107", "produto": "MP - F.T.E.BR 12 GRAN", "mp": ""},
  {"cod": "1003134", "produto": "MP - 03 17 00 GR", "mp": ""},
  {"cod": "1003136", "produto": "MP - 02 18 00  + 200 KG FMA BR 132 GR", "mp": "02 18"},
  {"cod": "1003141", "produto": "MP - 04 14 08 GR + 13CA + 8S", "mp": "04 14 08"},
  {"cod": "1013603", "produto": "MP - SSGR 19/15P2O5+18CA+10S(REPROCESSO)", "mp": "SSP 19"},
  {"cod": "1013831", "produto": "MP - S9 10 46 00 - MICROESSENTIALS GR", "mp": "S9 10 46"},
  {"cod": "1015347", "produto": "MP - 02 20 00 + 20 CA + 10 S GR", "mp": ""},
  {"cod": "1015430", "produto": "MP - COBRE 10", "mp": ""},
  {"cod": "1015760", "produto": "MP - 11 44 00 GR", "mp": "11 44"},
  {"cod": "1015850", "produto": "MP - SULFATO DE AMONIO FAR. 21N  23S", "mp": "SAM Fr"},
  {"cod": "1015866", "produto": "MP - 02 18 00 GR (MINERAL COMPLEXO)", "mp": "02 18"},
  {"cod": "1016092", "produto": "MP - SULFATO DE AMONIO GR 21N 23S", "mp": ""},
  {"cod": "1016127", "produto": "MP - MICRO MIX(S70 B1 CU 1 MN3 ZN3)-NOVO", "mp": ""},
  {"cod": "1016150", "produto": "MP - NP 12 46 00", "mp": ""},
  {"cod": "1016153", "produto": "MP - NPK 15 15 15 GRANULADO", "mp": ""},
  {"cod": "1016170", "produto": "MP - MICRO B6 ZN6", "mp": ""},
  {"cod": "1016171", "produto": "MP - MICRO B1,6 CU1,6 MN8 ZN12", "mp": ""},
  {"cod": "1016178", "produto": "MP - AGRAMIX MICRO B1,5 CU1,5 MN5 ZN5", "mp": ""},
  {"cod": "1016181", "produto": "MP - MICRO B6 MN2 ZN6", "mp": ""},
  {"cod": "1016308", "produto": "MP - SSGR 20/18P2O5 + 23CA+12S GR", "mp": ""},
  {"cod": "1016380", "produto": "MP - SSGR 19/15P2O5+20CA+13S", "mp": ""},
  {"cod": "1016695", "produto": "MP - SSGR 18/15P2O5 + 20CA+12S", "mp": ""},
  {"cod": "1016782", "produto": "MP - BOROMOL 4,8 B + 0,48 MO GR", "mp": ""},
  {"cod": "1016785", "produto": "MP - BORO  4B GR", "mp": "Boro 4"},
  {"cod": "1016792", "produto": "MP - UREIA  46 N GRANULADA", "mp": "Ureia"},
  {"cod": "1016809", "produto": "MP - BORO  6B GR", "mp": ""},
  {"cod": "1016810", "produto": "MP - ZINCO 06 GR", "mp": ""},
  {"cod": "1016811", "produto": "MP - ZINCO 08 GR", "mp": "Zinco 8"},
  {"cod": "1017068", "produto": "MP - CLORETO POTASSIO 60.5K2O GRANULADO", "mp": "KCL 60,5"},
  {"cod": "1017152", "produto": "MP - FOSF.MON.MAP GR 11N 52/44P2O5 BRANC", "mp": ""},
  {"cod": "1017154", "produto": "MP - 02 19 21 GR", "mp": ""},
  {"cod": "1017209", "produto": "MP - ASPIRE 00 00 58 + 0,5 B GR", "mp": "Aspire"},
  {"cod": "1017214", "produto": "MP - 00 23 00 COMP23/17P2O5+17CA+10S GR", "mp": "00 23 00"},
  {"cod": "1017337", "produto": "MP - SULFATO DE AMONIO GR 20N 23S COMPAC", "mp": "SAM 20N 23S COMPAC"},
  {"cod": "1017338", "produto": "MP - SULFATO DE AMONIO GR 21N 23S COMPAC", "mp": "Sam 21 23"},
  {"cod": "1017339", "produto": "MP - SULF. DE AMONIO 21N 24S COMPAC  GR", "mp": "SAM 21 Compac"},
  {"cod": "1017439", "produto": "MP - MES SZ 11 40 00 + 6 S", "mp": ""},
  {"cod": "1017456", "produto": "MP - CLORETO POTASSIO 60.5K2O FARELADO", "mp": ""},
  {"cod": "1017556", "produto": "MP - ATHOS 02 19 21 + 0,2 ZN + 0,1 B", "mp": ""},
  {"cod": "1017559", "produto": "MP - ATHOS 03 24 06 + 0,2 ZN + 0,1 B", "mp": ""},
  {"cod": "1017617", "produto": "MP - 03 19 00 GR + 16CA + 10S", "mp": ""},
  {"cod": "1017618", "produto": "MP - SSGR 18/16P2O5 + 16CA + 11S", "mp": ""},
  {"cod": "1017627", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1017733", "produto": "MP - FOSF DIAMON 18N 46/40P2O5 FARELADO", "mp": ""},
  {"cod": "1017834", "produto": "MP - BASICA PRO 22% CA + 4% SI", "mp": ""},
  {"cod": "1017860", "produto": "MP - CLORETO DE POTASSIO STD - FERT", "mp": ""},
  {"cod": "1017930", "produto": "MP - KMAG 21,5K2O 21S 10,5MG GR", "mp": "KMAG"},
  {"cod": "1017976", "produto": "MP - SUPERFOSFATO DE CALCIO 18/20+12S", "mp": ""},
  {"cod": "1018025", "produto": "MP - ATHOS 02 19 19 + 0,1 B + 0,2 ZN", "mp": ""},
  {"cod": "1018034", "produto": "MP - CLORETO POTASSIO 60.5K2O FAR RED", "mp": ""},
  {"cod": "1018081", "produto": "MP - CLORETO POTASSIO 62.0K2O WHITE FINE", "mp": ""},
  {"cod": "1018093", "produto": "MP - ATHOS 03 32 08 + 0,2 ZN + 0,1 B GR", "mp": ""},
  {"cod": "1018163", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1018194", "produto": "MP - ASPIRE 00 00 58 + 0,5 B - STD", "mp": ""},
  {"cod": "1018198", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1018199", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1018207", "produto": "MP - CLORETO POTASSIO 60.5K2O RED FINE", "mp": ""},
  {"cod": "1018315", "produto": "MP - MIB209 6%B + 2%MN + 6%ZN", "mp": "MIB209"},
  {"cod": "1018316", "produto": "MP - 02 18 00+200 KG FMA BR 132 (2) GR", "mp": "02 18"},
  {"cod": "1018329", "produto": "MP - S15 13 33 00 - MICROESSENTIALS", "mp": ""},
  {"cod": "1018337", "produto": "MP - SSGR 20/17P2O5 + 16CA + 10S IMP GR", "mp": "SSP 20"},
  {"cod": "1018338", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1018339", "produto": "MP - KMAG GR  22K 22S 10MG -GRANUL", "mp": ""},
  {"cod": "1018345", "produto": "MP - SULFATO DE AMONIO GR 20.5N 22S COMP", "mp": ""},
  {"cod": "1018551", "produto": "MP - FOSFATO ACIDULAD 15/9P2O5+15CA+10S", "mp": "SSP Pó"},
  {"cod": "1018561", "produto": "MP - FOSF.MON.MAP GR 11N 52/44P2O5", "mp": ""},
  {"cod": "1018609", "produto": "MP - NUREA 46 N", "mp": ""},
  {"cod": "1018624", "produto": "MP - CLORETO POTASSIO 60.5K2O MIRITITUBA", "mp": ""},
  {"cod": "1018626", "produto": "MP - S9 10 46 00 - MIRITITUBA", "mp": ""},
  {"cod": "1018651", "produto": "MP - SULF. DE AMONIO 20.5N 23S COMP GR", "mp": "SAM 20.5"},
  {"cod": "1018755", "produto": "MP - KMAG GR  22K 22S 10MG -GRANUL", "mp": ""},
  {"cod": "1019669", "produto": "MP - 02 18 00 + 1B + 2,0MN + 6S + 2,0ZN", "mp": ""},
  {"cod": "1019716", "produto": "MP - FOSF.MON. - MAP FAR. 10N 51/44P2O5", "mp": ""},
  {"cod": "1019738", "produto": "MP - SSGR 18/16P2O5+16CA+10S", "mp": ""},
  {"cod": "1019740", "produto": "MP - 10 45 00 GR", "mp": "10 45 00"},
  {"cod": "1019798", "produto": "MP - UREIA 46 N - S/ESPECIFICACAO", "mp": ""},
  {"cod": "1019856", "produto": "MP - SSGR 18,5/16P2O5+21CA+11S GR", "mp": "SSP 18,5"},
  {"cod": "1019990", "produto": "MP - SSGR 19/16P2O5+16CA+10S GR", "mp": "SSP 19"},
  {"cod": "1020001", "produto": "MP - POLYSULPHATE 14K2O + 3,7MG", "mp": ""},
  {"cod": "1020029", "produto": "MP - SSGR 18,5/16P2O5+16CA+10S", "mp": ""},
  {"cod": "1020116", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1020117", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1020158", "produto": "MP - 00 20 00 + 0,1B+0,06CU+0,2MN+0,2ZN", "mp": ""},
  {"cod": "1020297", "produto": "MP - 10 46 00 - 7,5%S GR", "mp": ""},
  {"cod": "1020306", "produto": "MP - NP 10 40 00", "mp": ""},
  {"cod": "1020340", "produto": "MP - CLORETO POTASSIO 60.5K2O S/ESPECIFI", "mp": ""},
  {"cod": "1020396", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1020404", "produto": "MP - KMAG GR  22K 22S 10MG -GRANUL", "mp": ""},
  {"cod": "1020405", "produto": "MP - KMAG GR  22K 22S 10MG -GRANUL", "mp": ""},
  {"cod": "1020406", "produto": "MP - KMAG GR  22K 22S 10MG -GRANUL", "mp": ""},
  {"cod": "1020407", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1020408", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1020409", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1020410", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1020435", "produto": "MP - 02 18 00 NEUTRAL +200KG FMA BR132GR", "mp": "02 18"},
  {"cod": "1020482", "produto": "MP - S9Z 10 45 00 0,5ZN MES PRO", "mp": "MES09WZ"},
  {"cod": "1020539", "produto": "MP - F.TE.BR12 50%", "mp": ""},
  {"cod": "1020557", "produto": "MP - FOSF.MON.MAP 10,5N 51,5/44P2O5 GR", "mp": ""},
  {"cod": "1020559", "produto": "MP - SUPERF.TRIPLO 45,5/36 P2O5 +10 CA G", "mp": ""},
  {"cod": "1020674", "produto": "MP - S9Z 10 45 00 0,5ZN MES PRO", "mp": ""},
  {"cod": "1020675", "produto": "MP - SULFATO BLUE COMPACTADO 21N 24S", "mp": "Sam Blue"},
  {"cod": "1020756", "produto": "MP - 10 45 00 GR + 2 S", "mp": ""},
  {"cod": "1020834", "produto": "MP - S9Z 10 45 00 + 9S + 0,5ZN MES PRO", "mp": ""},
  {"cod": "1020909", "produto": "MP - 00 20 00 + 16CA + 10S GR", "mp": ""},
  {"cod": "1021104", "produto": "MP - MICRO CASADO 10 CU + 10 ZN", "mp": ""},
  {"cod": "1021174", "produto": "MP - FERT ORGANICO 0,5N + 15COT", "mp": "Fert Organico"},
  {"cod": "1021181", "produto": "MP - FOSF.MON.MAP 09N 49/44P2O5 GR", "mp": ""},
  {"cod": "1021387", "produto": "MP - 00 41,5 00", "mp": ""},
  {"cod": "1021388", "produto": "MP - 00 43 00", "mp": "TSP 43"},
  {"cod": "2000017", "produto": "MP - ROCHA FOF.- BAYOVAR - 64/7", "mp": ""},
  {"cod": "2000019", "produto": "MP - ROCHA FOSFATICA KHOURIGBA - K10", "mp": ""},
  {"cod": "2000022", "produto": "MP - ROCHA FOSFATICA 28(P2O5)-KHOURIBGA", "mp": ""},
  {"cod": "2000023", "produto": "MP - ROCHA  FOSFATICA- ALGERIA-BPL 66/68", "mp": ""},
  {"cod": "2000026", "produto": "MP - ROCHA FOSFATICA 30(P2O5)", "mp": ""},
  {"cod": "2000035", "produto": "MP - SSPO 18/15P2O5+17CA+10S- P/INDUSTR", "mp": ""},
  {"cod": "2000164", "produto": "MP - ROCHA ELANDSFONTEIN", "mp": ""},
  {"cod": "3000030", "produto": "MP - ACIDO SULFURICO", "mp": ""},
  {"cod": "3000032", "produto": "MP - CALCARIO DOLOMITICO", "mp": ""},
  {"cod": "3000035", "produto": "MP - ENXOFRE", "mp": ""},
  {"cod": "3000039", "produto": "MP - DUSTROL 5012", "mp": ""},
  {"cod": "3000042", "produto": "MP - ANTIDUSTING START SC ADFERT", "mp": "Antdusting"},
  {"cod": "3000045", "produto": "MP - OLEO BPF", "mp": ""},
  {"cod": "3000062", "produto": "MP - OLEO DUSTROL 3050", "mp": ""},
  {"cod": "3000075", "produto": "MP - INIBIDOR DE UREASE", "mp": "Inibidor"},
  {"cod": "3000100", "produto": "MP - START RED ADFERT", "mp": ""},
  {"cod": "3000101", "produto": "MP - R-COAT ANTIEMBLOCAMENTE ADFERT", "mp": "R-Coat"},
  {"cod": "3000104", "produto": "MP - ANTIDUST CHEMTEC", "mp": ""},
  {"cod": "3000105", "produto": "MP - MAX OIL M-NPK", "mp": "Max Oil"},
  {"cod": "3000106", "produto": "MP - SK FERT AD 460", "mp": ""},
  {"cod": "3000108", "produto": "MP - ENZYFERT EF01", "mp": ""},
  {"cod": "3000109", "produto": "MP - MICROSTICKERS MS-23006", "mp": "MICROSTICKERS"},
  {"cod": "3000110", "produto": "MP - FLUIDIRAM 5035 ARRMAZ", "mp": ""},
  {"cod": "3000111", "produto": "MP - ADITIVO REC ANTIDUST MAX OIL GRMO", "mp": ""},
  {"cod": "3000113", "produto": "MP - ANTIDUSTING START BLACK ADITIVO", "mp": ""},
  {"cod": "3000114", "produto": "MP - DUSTROL 5526", "mp": ""},
  {"cod": "3000115", "produto": "MP - DUSTROL 5525", "mp": ""},
  {"cod": "3000123", "produto": "MP - ECO COAT BLACK", "mp": ""},
  {"cod": "3000124", "produto": "MP - ECO COAT RED", "mp": ""},
  {"cod": "3000125", "produto": "MP - ECO COAT GREEN (NBPT)", "mp": ""},
  {"cod": "3000128", "produto": "MP - ACIDO SULFURICO NACIONAL", "mp": ""},
  {"cod": "3000130", "produto": "MP - PROTETOR NITROG POLIMERO", "mp": ""},
  {"cod": "3000131", "produto": "MP - ADITIVO ANTIAGLOMERANTE BIOFLOW", "mp": ""},
  {"cod": "3000132", "produto": "MP - ANTIDUSTING ADS", "mp": ""},
  {"cod": "3000133", "produto": "MP - MATERIA ORGANICA", "mp": ""},
  {"cod": "3000134", "produto": "MP - UREMAX NBPT", "mp": ""},
  {"cod": "3000135", "produto": "MP - VOLIT ADITIVO", "mp": ""},
  {"cod": "8001698", "produto": "MP - CLORETO DE POTASSIO GR 62K2O-BRANCO", "mp": ""},
  {"cod": "1021719", "produto": "MP - 00 18 00 COMP18/13P2O5+19Ca+11S GR", "mp": "00 18 00"},
  {"cod": "3000252", "produto": "Kiesirita Gr", "mp": "Kiesirita Gr"},
  {"cod": "1022266", "produto": "MP - S9 10 46 00 - OFF SPEC", "mp": "S9 10 46 Off Spec"},
  {"cod": "1016857", "produto": "MICRO CASADO 2,0% Zn + 0,6% B + 2,0% Mn", "mp": "MICRO CASADO"},
  {"cod": "8000267", "produto": "ETF06", "mp": "ETF06"},
  {"cod": "8000273", "produto": "ETF08B", "mp": "ETF08B"},
  {"cod": "8000278", "produto": "ETF09", "mp": "ETF09"},
  {"cod": "8000279", "produto": "ETF11", "mp": "ETF11"},
  {"cod": "8000286", "produto": "ETF10", "mp": "ETF10"},
  {"cod": "8000396", "produto": "ETF12", "mp": "ETF12"},
  {"cod": "3000293", "produto": "MP - NITROGUARD NBPT CP27", "mp": "NITROGUARD NBPT CP27"},
  {"cod": "1021528", "produto": "MPANITRO 46 00 00 UR", "mp": "MPANITRO 46 00 00 UR"},
  {"cod": "1000195", "produto": "MP - S10 12 40 00 - Microessentials Gr", "mp": "S10 12 40 00"},
  {"cod": "1022496", "produto": "MP - 08 40 00 + 5S", "mp": "MP - 08 40 00 + 5S"},
  {"cod": "3000312", "produto": "MP - Sulfato de Magnésio GR 15MG 20s", "mp": "SULFATO DE MAGNÉSIO"},
  {"cod": "1017020", "produto": "MINERAL MISTO I 6000", "mp": "MINERAL MISTO I"},
  {"cod": "1017026", "produto": "MINERAL MISTO I 6280", "mp": "MINERAL MISTO I"},
  {"cod": "116650",  "produto": "MS15E 12 16 14 S15", "mp": "MS15E 12 16 14 S15"},
  {"cod": "1023005", "produto": "MP - BioblendGr 42/32P2O5 +10Ca +1COT", "mp": "Bioblend"},
]


# ── MODEL ────────────────────────────────────────────────────────────────────
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
    pedido = db.Column(db.String(200))
    item = db.Column(db.String(50))
    valor_unit = db.Column(db.Float)
    troca_nf = db.Column(db.String(30), default='Não')
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


# ── EMAIL ────────────────────────────────────────────────────────────────────
def _enviar_smtp(html_body, assunto):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = SMTP_FROM
    msg["To"]      = ", ".join(EMAIL_DESTINATARIOS)
    if EMAIL_CC:
        msg["Cc"]  = ", ".join(EMAIL_CC)
    msg.attach(MIMEText(html_body, "html"))
    destinatarios = EMAIL_DESTINATARIOS + EMAIL_CC
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_FROM, destinatarios, msg.as_string())


def _build_tabela_html(registros, titulo, extra_obs=""):
    linhas = ""
    for r in registros:
        urg = "🚨 " if r.get('urgente') else ""
        hor = r['horario_corte'] or "—"
        # horário de corte em vermelho se preenchido
        hor_html = f'<span style="color:#c0392b;font-weight:bold">{hor}</span>' if r.get('horario_corte') else "—"
        linhas += f"""
        <tr>
          <td>{r['data_br']}</td>
          <td>{r['origem']}</td>
          <td>{r['destino']}</td>
          <td>{urg}{r['mp'] or ''}</td>
          <td>{r['periodo_operacao'] or '—'}</td>
          <td>{hor_html}</td>
          <td>{int(r['quantidade']) if r['quantidade'] else '—'}</td>
          <td>{r['tipo_veiculo'] or '—'}</td>
          <td>{r['programacao_vol'] or '—'}</td>
          <td>{r['pedido'] or '—'}</td>
          <td>{r['item'] or '—'}</td>
          <td>{('R$ ' + f"{r['valor_unit']:,.2f}".replace(',','X').replace('.',',').replace('X','.')) if r['valor_unit'] else '—'}</td>
          <td>{r['troca_nf'] or 'Não'}</td>
          <td>{r['operacao'] or '—'}</td>
          <td>{r['transportadora'] or '—'}</td>
        </tr>"""

    obs_block = f"<p style='margin:12px 0'><strong>Observação:</strong> {extra_obs}</p>" if extra_obs else ""

    return f"""
    <html><body style="font-family:Arial,sans-serif;color:#222;font-size:13px">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td style="background:#155724;padding:14px 20px">
          <span style="color:#fff;font-size:17px;font-weight:bold">🌱 Mosaic Supply Chain</span>
        </td></tr>
      </table>
      <div style="padding:16px 20px">
        <h2 style="color:#155724;margin:0 0 4px">{titulo}</h2>
        {obs_block}
      </div>
      <div style="padding:0 20px 20px">
        <table border="0" cellpadding="6" cellspacing="0" width="100%"
               style="border-collapse:collapse;font-size:12px">
          <thead>
            <tr style="background:#155724;color:#fff">
              <th>Data</th><th>Origem</th><th>Destino</th><th>MP</th>
              <th>Período</th><th>H. Corte</th><th>Qtd</th><th>Tipo</th>
              <th>Vol. (t)</th><th>Pedido</th><th>Item</th><th>Valor Unit.</th>
              <th>Troca NF</th><th>Operação</th><th>Transportadora</th>
            </tr>
          </thead>
          <tbody>{"".join(
            f'<tr style="background:{"#f9f9f9" if i%2==0 else "#fff"}">{linhas.split("</tr>")[i]}</tr>'
            for i in range(len(registros))
          ) if False else linhas}
          </tbody>
        </table>
      </div>
      <p style="padding:0 20px;font-size:10px;color:#888">
        Gerado automaticamente pelo sistema Mosaic Supply Chain.
      </p>
    </body></html>"""


# ── HELPER ──────────────────────────────────────────────────────────────────
def _to_float(v):
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _apply_payload(obj, payload):
    """Aplica campos do payload em um objeto Programacao."""
    data_str = payload.get('data')
    if data_str:
        obj.data = datetime.strptime(data_str, '%Y-%m-%d').date()
    obj.origem           = payload.get('origem', obj.origem)
    obj.destino          = payload.get('destino', obj.destino)
    obj.cod              = payload.get('cod', obj.cod)
    obj.produto          = payload.get('produto', obj.produto)
    obj.mp               = payload.get('mp', obj.mp)
    obj.periodo_operacao = payload.get('periodo_operacao', obj.periodo_operacao)
    obj.horario_corte    = payload.get('horario_corte', obj.horario_corte)
    obj.tipo_veiculo     = payload.get('tipo_veiculo', obj.tipo_veiculo)
    obj.pedido           = payload.get('pedido', obj.pedido)
    obj.item             = payload.get('item', obj.item)
    obj.troca_nf         = payload.get('troca_nf', obj.troca_nf)
    obj.operacao         = payload.get('operacao', obj.operacao)
    obj.obs              = payload.get('obs', obj.obs)
    obj.transportadora   = payload.get('transportadora', obj.transportadora)
    obj.urgente          = bool(payload.get('urgente', obj.urgente))
    obj.status           = payload.get('status', obj.status)
    if 'quantidade' in payload:
        obj.quantidade = _to_float(payload['quantidade'])
    if 'programacao_vol' in payload:
        obj.programacao_vol = _to_float(payload['programacao_vol'])
    if 'valor_unit' in payload:
        obj.valor_unit = _to_float(payload['valor_unit'])
    obj.atualizado_em = datetime.utcnow()


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


# ── DASHBOARD ────────────────────────────────────────────────────────────────
@app.route('/api/dashboard')
def dashboard():
    hoje   = date.today()
    amanha = hoje + timedelta(days=1)

    total        = Programacao.query.count()
    pendentes    = Programacao.query.filter_by(status='Pendente').count()
    em_andamento = Programacao.query.filter_by(status='Em andamento').count()
    confirmados  = Programacao.query.filter_by(status='Confirmado').count()
    urgentes     = Programacao.query.filter_by(urgente=True).count()
    hoje_c       = Programacao.query.filter_by(data=hoje).count()
    amanha_c     = Programacao.query.filter_by(data=amanha).count()
    vol_res      = db.session.query(func.sum(Programacao.programacao_vol)).scalar()
    volume_total = round(vol_res or 0, 2)

    def agrupar(col, label, limit=6):
        rows = (db.session.query(col, func.count(Programacao.id))
                .group_by(col).order_by(func.count(Programacao.id).desc()).limit(limit).all())
        return [{label: v or '—', 'count': c} for v, c in rows]

    return jsonify({
        'total': total, 'pendentes': pendentes, 'em_andamento': em_andamento,
        'confirmados': confirmados, 'urgentes': urgentes, 'hoje': hoje_c,
        'amanha': amanha_c, 'volume_total': volume_total,
        'por_operacao':       agrupar(Programacao.operacao,        'operacao'),
        'por_destino':        agrupar(Programacao.destino,         'destino'),
        'por_transportadora': agrupar(Programacao.transportadora,  'transportadora'),
    })


# ── CRUD ─────────────────────────────────────────────────────────────────────
@app.route('/api/programacoes', methods=['GET'])
def listar():
    q = Programacao.query
    if v := request.args.get('data'):
        try:
            q = q.filter_by(data=datetime.strptime(v, '%Y-%m-%d').date())
        except ValueError:
            return jsonify({'error': 'Data inválida'}), 400
    if v := request.args.get('origem'):
        q = q.filter(Programacao.origem.ilike(f'%{v}%'))
    if v := request.args.get('destino'):
        q = q.filter(Programacao.destino.ilike(f'%{v}%'))
    if v := request.args.get('status'):
        q = q.filter_by(status=v)
    if request.args.get('urgente', '').lower() == 'true':
        q = q.filter_by(urgente=True)
    rows = q.order_by(Programacao.data.desc(), Programacao.criado_em.desc()).all()
    return jsonify([r.to_dict() for r in rows])


@app.route('/api/programacoes/<int:id>', methods=['GET'])
def get_prog(id):
    return jsonify(Programacao.query.get_or_404(id).to_dict())


@app.route('/api/programacoes', methods=['POST'])
def criar():
    p = request.json or {}
    if not p.get('data') or not p.get('origem') or not p.get('destino') or not p.get('produto'):
        return jsonify({'success': False, 'error': 'Campos obrigatórios: data, origem, destino, produto'}), 400
    try:
        data_obj = datetime.strptime(p['data'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Data inválida'}), 400
    nova = Programacao(
        data=data_obj, origem=p.get('origem'), destino=p.get('destino'),
        produto=p.get('produto'), troca_nf=p.get('troca_nf', 'Não'),
        urgente=bool(p.get('urgente', False)), status=p.get('status', 'Pendente'),
    )
    _apply_payload(nova, p)
    db.session.add(nova)
    db.session.commit()
    return jsonify({'success': True, 'id': nova.id})


@app.route('/api/programacoes/<int:id>', methods=['PUT'])
def editar(id):
    r = Programacao.query.get_or_404(id)
    p = request.json or {}

    # Captura snapshot antes da edição para o email de alteração
    antes = r.to_dict()

    _apply_payload(r, p)
    db.session.commit()

    # Email automático de alteração (não bloqueia a resposta se falhar)
    notificar = p.get('notificar_alteracao', False)
    if notificar:
        try:
            _enviar_email_alteracao(antes, r.to_dict())
        except Exception:
            pass  # email falhou silenciosamente — não impede o save

    return jsonify({'success': True})


@app.route('/api/programacoes/<int:id>', methods=['DELETE'])
def deletar(id):
    r = Programacao.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    return jsonify({'success': True})


# ── EMAIL DE ALTERAÇÃO ────────────────────────────────────────────────────────
def _enviar_email_alteracao(antes, depois):
    """Envia um email de complemento/alteração destacando os campos modificados."""
    campos_label = {
        'data_br': 'Data', 'origem': 'Origem', 'destino': 'Destino',
        'mp': 'MP', 'produto': 'Produto', 'cod': 'Cód.',
        'periodo_operacao': 'Período', 'horario_corte': 'H. Corte',
        'quantidade': 'Quantidade', 'tipo_veiculo': 'Tipo Veículo',
        'programacao_vol': 'Volume (t)', 'pedido': 'Pedido', 'item': 'Item',
        'valor_unit': 'Valor Unit.', 'troca_nf': 'Troca NF',
        'operacao': 'Operação', 'transportadora': 'Transportadora',
        'urgente': 'Urgente', 'status': 'Status', 'obs': 'Observações',
    }
    ignorar = {'criado_em', 'atualizado_em'}

    linhas_diff = ""
    for campo, label in campos_label.items():
        if campo in ignorar:
            continue
        v_antes  = antes.get(campo)
        v_depois = depois.get(campo)
        if str(v_antes or '') != str(v_depois or ''):
            linhas_diff += f"""
            <tr>
              <td style="padding:6px 10px;border-bottom:1px solid #eee;font-weight:600">{label}</td>
              <td style="padding:6px 10px;border-bottom:1px solid #eee;color:#c0392b;
                         text-decoration:line-through">{v_antes or '—'}</td>
              <td style="padding:6px 10px;border-bottom:1px solid #eee;color:#155724;
                         font-weight:bold">{v_depois or '—'}</td>
            </tr>"""

    if not linhas_diff:
        return  # nada mudou, não envia

    data_fmt   = depois.get('data_br', '—')
    origem     = depois.get('origem', '—')
    destino    = depois.get('destino', '—')
    mp         = depois.get('mp') or depois.get('produto', '—')
    prog_id    = depois.get('id', '—')

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#222;font-size:13px">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td style="background:#155724;padding:14px 20px">
          <span style="color:#fff;font-size:17px;font-weight:bold">🌱 Mosaic Supply Chain</span>
        </td></tr>
      </table>
      <div style="padding:16px 20px">
        <h2 style="color:#c0392b;margin:0 0 4px">⚠️ Alteração na Programação #{prog_id}</h2>
        <p style="color:#555;margin:4px 0 16px">
          <strong>{data_fmt}</strong> · {origem} → {destino} · <strong>{mp}</strong>
        </p>
        <table border="0" cellpadding="0" cellspacing="0" width="100%"
               style="border-collapse:collapse;font-size:13px;max-width:600px">
          <thead>
            <tr style="background:#f4f4f4">
              <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd">Campo</th>
              <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd">Antes</th>
              <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #ddd">Depois</th>
            </tr>
          </thead>
          <tbody>{linhas_diff}</tbody>
        </table>
      </div>
      <p style="padding:0 20px;font-size:10px;color:#888">
        Alteração registrada automaticamente pelo sistema Mosaic Supply Chain.
      </p>
    </body></html>"""

    assunto = f"[Mosaic] Alteração na Programação #{prog_id} — {data_fmt} — {mp}"
    _enviar_smtp(html, assunto)


# ── EMAIL PROGRAMAÇÃO ─────────────────────────────────────────────────────────
@app.route('/api/enviar-email', methods=['POST'])
def enviar_email():
    payload     = request.json or {}
    data_ref    = payload.get('data')
    ids_sel     = payload.get('ids')
    extra_obs   = payload.get('obs', '')

    if not data_ref:
        return jsonify({'success': False, 'error': 'Data não informada'}), 400
    try:
        d = datetime.strptime(data_ref, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Data inválida'}), 400

    q = Programacao.query.filter_by(data=d)
    if ids_sel:
        q = q.filter(Programacao.id.in_(ids_sel))
    registros = q.order_by(Programacao.criado_em).all()
    if not registros:
        return jsonify({'success': False, 'error': 'Nenhuma programação para esta data'}), 404

    data_fmt  = d.strftime('%d/%m/%Y')
    titulo    = f"Programação de MP — {data_fmt}"
    html_body = _build_tabela_html([r.to_dict() for r in registros], titulo, extra_obs)
    assunto   = f"[Mosaic] Programação de MP — {data_fmt}"

    try:
        _enviar_smtp(html_body, assunto)
        return jsonify({'success': True, 'message': f'Email enviado para {len(EMAIL_DESTINATARIOS)} destinatário(s)!'})
    except smtplib.SMTPAuthenticationError:
        return jsonify({'success': False, 'error': 'Erro de autenticação SMTP'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── INIT ─────────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5050, host='0.0.0.0')