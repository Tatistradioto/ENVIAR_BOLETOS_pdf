import re
import pdfplumber

# 🔎 Regex CNPJ padrão Brasil (mais flexível)
REGEX_CNPJ = r'(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})'

def limpar_cnpj(cnpj):
    """Remove tudo que não é número"""
    if not cnpj:
        return None
    return re.sub(r'\D', '', str(cnpj))

def extrair_texto_pdf(caminho_pdf):
    """Extrai todo texto do PDF com tratamento de erros"""
    texto = ""
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                conteudo = pagina.extract_text()
                if conteudo:
                    texto += conteudo + "\n"
                
                # Tenta extrair da tabela se não encontrar texto normal
                if not conteudo:
                    tabelas = pagina.extract_tables()
                    for tabela in tabelas:
                        for linha in tabela:
                            if linha and any(linha):
                                texto += " ".join([str(celula) for celula in linha if celula]) + "\n"
    except Exception as e:
        print(f"Erro ao ler PDF {caminho_pdf}: {e}")
        return ""
    
    return texto.upper()

def extrair_cnpj_cliente(caminho_pdf):
    """
    🎯 Versão melhorada - Retorna o CNPJ do cliente
    """
    texto = extrair_texto_pdf(caminho_pdf)
    
    # =========================
    # 🔹 PRIORIDADE 1 - PAGADOR / SACADO
    # =========================
    palavras_chave = ["PAGADOR", "SACADO", "SACADOR", "CLIENTE", "TOMADOR", "COMPRADOR"]
    
    for chave in palavras_chave:
        if chave in texto:
            # Pega o trecho após a palavra-chave
            trecho = texto.split(chave, 1)[1]
            
            # Limita o trecho para evitar pegar CNPJ do beneficiário
            for limite in ["BENEFICIÁRIO", "BENEFICIARIO", "CEDENTE", "NOSSO NÚMERO"]:
                if limite in trecho:
                    trecho = trecho.split(limite)[0]
            
            # Pega apenas as primeiras 500 caracteres
            trecho = trecho[:500]
            
            # Busca CNPJ no trecho
            cnpjs = re.findall(REGEX_CNPJ, trecho)
            if cnpjs:
                cnpj_limpo = limpar_cnpj(cnpjs[0])
                # Verifica se é um CNPJ válido (14 dígitos)
                if len(cnpj_limpo) == 14:
                    return cnpj_limpo
    
    # =========================
    # 🔹 PRIORIDADE 2 - CPF/CNPJ próximo a palavras-chave
    # =========================
    padroes_cnpj = [
        r'CPF/CNPJ[:\s]*(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})',
        r'CNPJ[:\s]*(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})',
        r'CPF[:\s]*(\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[\-\s]?\d{2})',
        r'DOCUMENTO[:\s]*(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})',
    ]
    
    for padrao in padroes_cnpj:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            cnpj_limpo = limpar_cnpj(match.group(1))
            if len(cnpj_limpo) in [11, 14]:  # CPF ou CNPJ
                return cnpj_limpo
    
    # =========================
    # 🔹 PRIORIDADE 3 - Qualquer CNPJ no documento
    # (mas evita o CNPJ da Araguaia)
    # =========================
    CNPJ_ARAGUAIA = "04005416000153"
    todos_cnpjs = re.findall(REGEX_CNPJ, texto)
    
    for cnpj in todos_cnpjs:
        cnpj_limpo = limpar_cnpj(cnpj)
        if len(cnpj_limpo) == 14 and cnpj_limpo != CNPJ_ARAGUAIA:
            return cnpj_limpo
    
    return None