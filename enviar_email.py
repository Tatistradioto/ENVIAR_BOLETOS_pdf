import os
import base64
import pickle
from datetime import datetime, timedelta
from email.message import EmailMessage

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def autenticar_gmail():
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


# 🔥 FUNÇÃO PARA GERAR MÊS SEGUINTE AUTOMÁTICO (BOLETOS)
def mes_seguinte():
    hoje = datetime.now()
    primeiro_dia_mes_atual = hoje.replace(day=1)
    proximo_mes = primeiro_dia_mes_atual + timedelta(days=32)
    return proximo_mes.strftime("%m/%Y")


# ===============================
# 💳 ENVIO DE BOLETO (NÃO ALTERADO)
# ===============================
def enviar_boleto(email_destino, caminho_pdf, nome_cliente, valor, vencimento):
    creds = autenticar_gmail()
    service = build('gmail', 'v1', credentials=creds)

    mes_referencia = datetime.now().strftime("%m/%Y")
    assunto = f"LOCAÇÃO DO SISTEMA – REF. MÊS {mes_referencia}"

    if not vencimento or vencimento == "None":
        vencimento = mes_seguinte()

    corpo = f"""
Olá, {nome_cliente},

Segue em anexo o boleto referente à locação do sistema no valor de R$ {valor}
com vencimento em {vencimento}.

Qualquer dúvida estamos à disposição.

Atenciosamente,
Setor Financeiro

---
Tatiana Stradioto  
Departamento Financeiro  
Araguaia Sistemas  
62 3933-4300  
araguaiasistemas.financeiro@gmail.com  
www.araguaiasistemas.com.br
"""

    mensagem = EmailMessage()
    mensagem['To'] = email_destino
    mensagem['From'] = 'me'
    mensagem['Subject'] = assunto
    mensagem.set_content(corpo)

    with open(caminho_pdf, 'rb') as f:
        arquivo = f.read()

    mensagem.add_attachment(
        arquivo,
        maintype='application',
        subtype='pdf',
        filename=os.path.basename(caminho_pdf)
    )

    raw = base64.urlsafe_b64encode(mensagem.as_bytes()).decode()
    service.users().messages().send(userId="me", body={'raw': raw}).execute()


# ==========================================================
# 🧾 ENVIO DE NOTA FISCAL (MÊS ATUAL — CORRIGIDO)
# ==========================================================
def enviar_nota_fiscal(email_destino, caminho_pdf, nome_cliente, numero_nf):
    creds = autenticar_gmail()
    service = build('gmail', 'v1', credentials=creds)

    # 🔥 AGORA USA MÊS ATUAL
    mes_referencia = datetime.now().strftime("%m/%Y")

    assunto = f"NOTA FISCAL DE SERVIÇO REF. LOCAÇÃO DO SISTEMA MÊS {mes_referencia}"

    if not nome_cliente or nome_cliente == "None":
        nome_cliente = "Cliente"

    if not numero_nf:
        numero_nf = "—"

    corpo = f"""
Olá, {nome_cliente},

Segue em anexo a Nota Fiscal nº {numero_nf}
referente à locação do sistema — mês {mes_referencia}.

Qualquer dúvida estamos à disposição.

Atenciosamente,
Setor Financeiro

---
Tatiana Stradioto  
Departamento Financeiro  
Araguaia Sistemas  
62 3933-4300  
araguaiasistemas.financeiro@gmail.com  
www.araguaiasistemas.com.br
"""

    mensagem = EmailMessage()
    mensagem['To'] = email_destino
    mensagem['From'] = 'me'
    mensagem['Subject'] = assunto
    mensagem.set_content(corpo)

    with open(caminho_pdf, 'rb') as f:
        arquivo = f.read()

    mensagem.add_attachment(
        arquivo,
        maintype='application',
        subtype='pdf',
        filename=os.path.basename(caminho_pdf)
    )

    raw = base64.urlsafe_b64encode(mensagem.as_bytes()).decode()
    service.users().messages().send(userId="me", body={'raw': raw}).execute()
