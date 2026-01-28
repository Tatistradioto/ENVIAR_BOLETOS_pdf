import re
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 🔐 PERMISSÕES DO APP
# contatos.readonly = ler contatos
# gmail.send = enviar boletos depois
SCOPES = [
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

# 📌 Regex para localizar CNPJ
REGEX_CNPJ = r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}'


def normalizar_cnpj(cnpj):
    return re.sub(r'\D', '', cnpj)


def autenticar_google():
    creds = None

    # 🔄 Usa login salvo
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 🔐 Se não estiver válido, pede login
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            SCOPES
        )

        # 🚀 Porta automática evita erro 403 e erro de porta ocupada
        creds = flow.run_local_server(port=0)

        # 💾 Salva token
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def buscar_email_por_cnpj(cnpj_alvo):
    cnpj_alvo = normalizar_cnpj(cnpj_alvo)

    creds = autenticar_google()
    service = build('people', 'v1', credentials=creds)

    resultados = service.people().connections().list(
        resourceName='people/me',
        pageSize=1000,
        personFields='names,emailAddresses,biographies'
    ).execute()

    contatos = resultados.get('connections', [])

    for pessoa in contatos:
        textos = []

        for nome in pessoa.get('names', []):
            textos.append(nome.get('displayName', ''))

        for bio in pessoa.get('biographies', []):
            textos.append(bio.get('value', ''))

        texto_unico = " ".join(textos)
        encontrados = re.findall(REGEX_CNPJ, texto_unico)

        for cnpj in encontrados:
            if normalizar_cnpj(cnpj) == cnpj_alvo:
                emails = pessoa.get('emailAddresses', [])
                
                # 🔥 AQUI MUDA TUDO
                lista_emails = [e.get('value') for e in emails if e.get('value')]
                
                if lista_emails:
                    return lista_emails  # ← AGORA RETORNA LISTA

    return None

