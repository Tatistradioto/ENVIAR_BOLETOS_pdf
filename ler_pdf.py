import re
import pdfplumber

CNPJ_ARAGUAIA = "04005416000153"

REGEX_CNPJ = r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}'
REGEX_DATA = r'\d{2}/\d{2}/\d{4}'
REGEX_VALOR = r'\d{1,3}(?:\.\d{3})*,\d{2}'


def limpar_cnpj(cnpj):
    return re.sub(r'\D', '', cnpj)


def extrair_texto_pdf(caminho_pdf):
    texto_completo = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                texto_completo += texto + "\n"
    return texto_completo.upper()


# ==========================================================
# 🔹 FUNÇÃO USADA PELOS BOLETOS (MANTIDA)
# ==========================================================
def extrair_dados_cliente(texto):

    nome_cliente = None
    cnpj_cliente = None
    valor = None
    vencimento = None

    # =====================================================
    # 🔥 SE FOR NOTA FISCAL → NÃO USA REGRA DE BOLETO
    # =====================================================
    if "DADOS DO TOMADOR DE SERVIÇOS" in texto:
        return None, None, None, None

    # =====================================================
    # 🧾 CNPJ DO CLIENTE (BOLETOS)
    # =====================================================
    for match in re.finditer(r'CNPJ/CPF:\s*(' + REGEX_CNPJ + ')', texto):

        cnpj = limpar_cnpj(match.group(1))

        if cnpj == CNPJ_ARAGUAIA:
            continue

        cnpj_cliente = cnpj

        trecho = texto[max(0, match.start()-200):match.start()]
        trecho = re.sub(r'VENCIMENTO.*', '', trecho)
        trecho = re.sub(r'VALOR DO DOCUMENTO.*', '', trecho)
        trecho = re.sub(r'\d{2}/\d{2}/\d{4}', '', trecho)

        linhas = [l.strip() for l in trecho.split("\n") if l.strip()]

        if linhas:
            nome_cliente = linhas[-1]
            nome_cliente = nome_cliente.replace("PAGADOR", "")
            nome_cliente = nome_cliente.replace("SACADOR", "")
            nome_cliente = nome_cliente.replace("SACADO", "")
            nome_cliente = nome_cliente.replace(":", "")
            nome_cliente = " ".join(nome_cliente.split())

        break

    # 💰 VALOR
    match_valor = re.search(r'VALOR DO DOCUMENTO.*?(' + REGEX_VALOR + ')', texto, re.DOTALL)
    if match_valor:
        valor = match_valor.group(1).replace(".", "").replace(",", ".")

    # 📅 VENCIMENTO
    trecho_venc = re.search(r'VENCIMENTO(.{0,60})', texto)
    if trecho_venc:
        datas = re.findall(REGEX_DATA, trecho_venc.group(1))
        if datas:
            vencimento = datas[0]

    return nome_cliente, cnpj_cliente, valor, vencimento


# ==========================================================
# 🧾 FUNÇÃO EXCLUSIVA PARA NOTA FISCAL
# ==========================================================
def extrair_dados_nf(texto):

    nome_cliente = None
    numero_nf = None
    cnpj_cliente = None

    # 🔢 Número da Nota Fiscal
    match_nf = re.search(r'N[ÚU]MERO DA NOTA FISCAL\s*(\d+)', texto)
    if not match_nf:
        match_nf = re.search(r'NOTA FISCAL.*?(\d{2,6})', texto, re.DOTALL)

    if match_nf:
        numero_nf = match_nf.group(1)

    # 🧾 BLOCO DO TOMADOR
    bloco_tomador = re.search(r'DADOS DO TOMADOR DE SERVIÇOS(.{0,500})', texto, re.DOTALL)
    if bloco_tomador:
        area = bloco_tomador.group(1)

        # CNPJ do tomador
        match_cnpj = re.search(REGEX_CNPJ, area)
        if match_cnpj:
            cnpj_cliente = limpar_cnpj(match_cnpj.group())

        # Razão social
        match_nome = re.search(r'RAZ[ÃA]O SOCIAL\s*:?\s*(.+)', area)
        if match_nome:
            nome_cliente = match_nome.group(1).strip()

    return nome_cliente, numero_nf, cnpj_cliente
