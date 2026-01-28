import re
import pdfplumber

# 🔎 Regex CNPJ padrão Brasil
REGEX_CNPJ = r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}'


def limpar_cnpj(cnpj):
    """Remove tudo que não é número"""
    return re.sub(r'\D', '', cnpj)


def extrair_texto_pdf(caminho_pdf):
    """Extrai todo texto do PDF"""
    texto = ""

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            conteudo = pagina.extract_text()
            if conteudo:
                texto += conteudo + "\n"

    return texto.upper()


def extrair_cnpj_cliente(caminho_pdf):
    """
    🎯 Retorna SOMENTE o CNPJ do PAGADOR (cliente)
    Funciona para Banco do Brasil, Inter, Caixa, Bradesco, Santander etc.
    """

    texto = extrair_texto_pdf(caminho_pdf)

    # =========================
    # 🔹 PRIORIDADE 1 → ÁREA DO PAGADOR
    # =========================
    if "PAGADOR" in texto:
        trecho = texto.split("PAGADOR", 1)[1]

        # Evita pegar CNPJ do beneficiário
        for marcador in ["BENEFICIÁRIO", "BENEFICIARIO", "SACADOR", "CEDENTE"]:
            if marcador in trecho:
                trecho = trecho.split(marcador)[0]

        cnpjs = re.findall(REGEX_CNPJ, trecho)
        if cnpjs:
            return limpar_cnpj(cnpjs[0])

    # =========================
    # 🔹 PRIORIDADE 2 → SACADO
    # =========================
    if "SACADO" in texto:
        trecho = texto.split("SACADO", 1)[1]
        cnpjs = re.findall(REGEX_CNPJ, trecho)
        if cnpjs:
            return limpar_cnpj(cnpjs[0])

    # =========================
    # 🔹 PRIORIDADE 3 → ÚLTIMO CNPJ DO BOLETO
    # (normalmente o cliente aparece por último)
    # =========================
    todos = re.findall(REGEX_CNPJ, texto)
    if todos:
        return limpar_cnpj(todos[-1])

    return None
