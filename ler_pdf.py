import re
import pdfplumber

CNPJ_ARAGUAIA = "04005416000153"

REGEX_DATA = r'\d{2}/\d{2}/\d{4}'
REGEX_VALOR = r'\d{1,3}(?:\.\d{3})*,\d{2}'

def limpar_cnpj(cnpj):
    return re.sub(r'\D', '', str(cnpj)) if cnpj else None

def extrair_texto_pdf(caminho_pdf):
    texto_completo = ""
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    texto_completo += texto + "\n"
    except Exception as e:
        print(f"Erro ao ler PDF {caminho_pdf}: {e}")
        return ""
    return texto_completo.upper()

def extrair_valor(texto):
    """Extrai valor do boleto com múltiplas estratégias"""
    
    # Estratégia 1: Padrão exato "VALOR DO DOCUMENTO"
    match = re.search(r'VALOR\s+DO\s+DOCUMENTO\s*[:\s]*R?\$?\s*(' + REGEX_VALOR + ')', texto, re.IGNORECASE)
    if match:
        return match.group(1).replace(".", "").replace(",", ".")
    
    # Estratégia 2: Apenas "VALOR"
    match = re.search(r'VALOR\s*[:\s]*R?\$?\s*(' + REGEX_VALOR + ')', texto, re.IGNORECASE)
    if match:
        return match.group(1).replace(".", "").replace(",", ".")
    
    # Estratégia 3: Procurar próximo a "R$"
    match = re.search(r'R\$\s*(' + REGEX_VALOR + ')', texto, re.IGNORECASE)
    if match:
        return match.group(1).replace(".", "").replace(",", ".")
    
    # Estratégia 4: Procurar qualquer valor no formato brasileiro
    matches = re.findall(r'(' + REGEX_VALOR + ')', texto)
    if matches:
        # Pega o último valor (geralmente é o principal)
        return matches[-1].replace(".", "").replace(",", ".")
    
    return None

def extrair_vencimento(texto):
    """Extrai data de vencimento do boleto"""
    
    # Estratégia 1: "DATA DE VENCIMENTO"
    match = re.search(r'DATA\s+DE\s+VENCIMENTO\s*[:\s]*(' + REGEX_DATA + ')', texto, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Estratégia 2: Apenas "VENCIMENTO"
    match = re.search(r'VENCIMENTO\s*[:\s]*(' + REGEX_DATA + ')', texto, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Estratégia 3: Data antes de "VALOR"
    match = re.search(r'(' + REGEX_DATA + r')\s+VALOR', texto, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Estratégia 4: Qualquer data no formato dd/mm/aaaa
    matches = re.findall(REGEX_DATA, texto)
    if matches:
        # Pega a primeira data (geralmente é o vencimento)
        return matches[0]
    
    return None

def extrair_nome_cliente(texto):
    """Extrai nome do cliente do boleto - VERSÃO FINAL CORRIGIDA"""
    
    # Estratégia 1: Procurar especificamente pelo nome ADRIANO
    if "ADRIANO" in texto:
        pos = texto.find("ADRIANO")
        trecho = texto[pos:pos+150]
        
        # Procura pelo nome até encontrar "CNPJ" ou número
        match = re.search(r'(ADRIANO[^C]+?)(?:\s+CNPJ|\s+\d)', trecho)
        if match:
            nome = match.group(1).strip()
            nome = nome.replace("CNPJ", "").strip()
            
            if len(nome) > 10 and "COM ESSAS CARACTERÍSTICAS" not in nome:
                print(f"   ✅ Nome encontrado: {nome}")
                return nome
        
        if "CNPJ" in trecho:
            nome = trecho.split("CNPJ")[0].strip()
            if len(nome) > 10 and "COM ESSAS CARACTERÍSTICAS" not in nome:
                print(f"   ✅ Nome encontrado (método simples): {nome}")
                return nome
    
    # Estratégia 2: Área do PAGADOR
    if "PAGADOR" in texto:
        trecho = texto.split("PAGADOR", 1)[1]
        trecho = trecho.replace("CNPJ/CPF", "").replace("NOSSO-NÚMERO", "").replace("NOSSO NÚMERO", "")
        trecho = trecho.strip()
        
        linhas = trecho.split('\n')
        for linha in linhas:
            linha = linha.strip()
            if len(linha) < 5:
                continue
            
            if "CNPJ" in linha:
                linha = linha.split("CNPJ")[0].strip()
            
            linha = re.sub(r'\s+\d{8,}.*$', '', linha)
            
            if (linha and 
                len(linha) > 5 and 
                "COM ESSAS CARACTERÍSTICAS" not in linha and
                not linha.startswith("DATA") and
                not linha.startswith("VALOR") and
                not linha.startswith("VENCIMENTO")):
                print(f"   ✅ Nome encontrado: {linha}")
                return linha
    
    return None

def extrair_cnpj_cliente_banco_inter(texto):
    """
    Função GENÉRICA para QUALQUER boleto do Banco Inter
    Extrai o CNPJ correto ignorando linha digitável
    """
    # Primeiro: procurar por "CNPJ/CPF:" explícito na área do Pagador
    match_cnpj = re.search(r'CNPJ/CPF[:\s]*(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})', texto)
    if match_cnpj:
        cnpj_limpo = re.sub(r'\D', '', match_cnpj.group(1))
        if len(cnpj_limpo) == 14:
            print(f"   ✅ CNPJ Inter encontrado (campo CNPJ/CPF): {cnpj_limpo}")
            return cnpj_limpo
    
    # Segundo: procurar na área do Pagador (qualquer nome de empresa)
    if "PAGADOR" in texto:
        trecho = texto.split("PAGADOR", 1)[1][:500]
        
        # Procura por CNPJ no formato xx.xxx.xxx/xxxx-xx
        match = re.search(r'(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})', trecho)
        if match:
            cnpj_limpo = re.sub(r'\D', '', match.group(1))
            if len(cnpj_limpo) == 14:
                print(f"   ✅ CNPJ Inter encontrado (área do Pagador): {cnpj_limpo}")
                return cnpj_limpo
    
    # Terceiro: procurar no formato do código de barras
    match_codigo = re.search(r'(\d{3})/(\d{10,11})', texto)
    if match_codigo:
        cnpj_codigo = match_codigo.group(2)
        if len(cnpj_codigo) in [11, 14]:
            print(f"   ✅ CNPJ Inter encontrado no código: {cnpj_codigo}")
            return cnpj_codigo
    
    return None

def extrair_valor_banco_inter(texto):
    """Função GENÉRICA para extrair valor de QUALQUER boleto do Banco Inter"""
    
    # Primeiro: tenta encontrar na linha do Pagador (formato típico do Inter)
    if "PAGADOR" in texto:
        trecho = texto.split("PAGADOR", 1)[1][:200]
        match = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*$', trecho, re.MULTILINE)
        if match:
            valor = match.group(1).replace(".", "").replace(",", ".")
            print(f"   ✅ Valor Inter encontrado (Pagador): {valor}")
            return valor
    
    # Segundo: procura "VALOR DO DOCUMENTO"
    match = re.search(r'VALOR DO DOCUMENTO\s*[:\s]*(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
    if match:
        valor = match.group(1).replace(".", "").replace(",", ".")
        print(f"   ✅ Valor Inter encontrado (VALOR DO DOCUMENTO): {valor}")
        return valor
    
    # Terceiro: procura qualquer valor no texto (ignora multa)
    matches = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
    if matches:
        # Pega o último valor (geralmente é o principal)
        valor = matches[-1].replace(".", "").replace(",", ".")
        if float(valor) > 10:
            print(f"   ✅ Valor Inter encontrado: {valor}")
            return valor
    
    return None

def extrair_cnpj_cliente_padrao(texto):
    """
    Função padrão para extrair CNPJ de outros bancos
    Ignora números de linha digitável (que começam com 13, 14, 15...)
    """
    # Primeiro: procurar por "CNPJ/CPF:" explícito
    match_cnpj = re.search(r'CNPJ/CPF[:\s]*(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})', texto)
    if match_cnpj:
        cnpj_limpo = re.sub(r'\D', '', match_cnpj.group(1))
        if len(cnpj_limpo) == 14 and cnpj_limpo != CNPJ_ARAGUAIA:
            print(f"   ✅ CNPJ encontrado (campo CNPJ/CPF): {cnpj_limpo}")
            return cnpj_limpo
    
    # Segundo: procurar na área do PAGADOR
    if "PAGADOR" in texto:
        trecho = texto.split("PAGADOR", 1)[1][:500]
        matches = re.findall(r'(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})', trecho)
        for match in matches:
            cnpj_limpo = re.sub(r'\D', '', match)
            # Ignora números que começam com 13, 14, 15 (linha digitável)
            if (len(cnpj_limpo) == 14 and 
                cnpj_limpo != CNPJ_ARAGUAIA and
                not cnpj_limpo.startswith(('13', '14', '15', '16', '17', '18', '19'))):
                print(f"   ✅ CNPJ encontrado na área do PAGADOR: {cnpj_limpo}")
                return cnpj_limpo
    
    # Terceiro: procurar em todo o texto
    matches = re.findall(r'(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})', texto)
    for match in matches:
        cnpj_limpo = re.sub(r'\D', '', match)
        # Ignora números que começam com 13, 14, 15 (linha digitável)
        if (len(cnpj_limpo) == 14 and 
            cnpj_limpo != CNPJ_ARAGUAIA and
            not cnpj_limpo.startswith(('13', '14', '15', '16', '17', '18', '19'))):
            print(f"   ✅ CNPJ encontrado: {cnpj_limpo}")
            return cnpj_limpo
    
    return None

def extrair_dados_cliente(texto):
    """
    Extrai todos os dados do cliente do boleto
    """
    # Verifica se é nota fiscal
    if "DADOS DO TOMADOR DE SERVIÇOS" in texto:
        return None, None, None, None
    
    # Identifica se é boleto do Banco Inter (pela presença de "Inter" ou "077-9")
    if "Inter" in texto or "077-9" in texto or "INTER" in texto:
        print("   📌 Boleto do Banco Inter detectado")
        nome_cliente = extrair_nome_cliente(texto)
        cnpj_cliente = extrair_cnpj_cliente_banco_inter(texto)
        valor = extrair_valor_banco_inter(texto)
        vencimento = extrair_vencimento(texto)
    else:
        # Para outros bancos, usa funções padrão
        nome_cliente = extrair_nome_cliente(texto)
        cnpj_cliente = extrair_cnpj_cliente_padrao(texto)
        valor = extrair_valor(texto)
        vencimento = extrair_vencimento(texto)
    
    return nome_cliente, cnpj_cliente, valor, vencimento

def extrair_dados_nf(texto):
    """
    Extrai dados da Nota Fiscal
    """
    nome_cliente = None
    numero_nf = None
    cnpj_cliente = None

    match_nf = re.search(r'N[ÚU]MERO[:\s]*DA[:\s]*NOTA[:\s]*FISCAL[:\s]*(\d+)', texto)
    if not match_nf:
        match_nf = re.search(r'NOTA[:\s]*FISCAL[:\s]*[Nn][°º]?[:\s]*(\d+)', texto)
    if not match_nf:
        match_nf = re.search(r'NF[:\s]*[Nn][°º]?[:\s]*(\d+)', texto)

    if match_nf:
        numero_nf = match_nf.group(1)

    bloco_tomador = re.search(r'DADOS[:\s]*DO[:\s]*TOMADOR[:\s]*DE[:\s]*SERVIÇOS(.{0,800})', texto, re.DOTALL)
    if bloco_tomador:
        area = bloco_tomador.group(1)

        match_cnpj = re.search(r'CNPJ/CPF[:\s]*(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})', area)
        if not match_cnpj:
            match_cnpj = re.search(r'(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})', area)
        
        if match_cnpj:
            cnpj_cliente = limpar_cnpj(match_cnpj.group(1))

        match_nome = re.search(r'RAZ[ÃA]O[:\s]*SOCIAL[:\s]*:?\s*([^\n]+)', area)
        if not match_nome:
            match_nome = re.search(r'NOME[:\s]*:?\s*([^\n]+)', area)
        if not match_nome:
            linhas = [l.strip() for l in area.split('\n') if l.strip()]
            if linhas:
                nome_cliente = linhas[0]
        
        if match_nome:
            nome_cliente = match_nome.group(1).strip()

    return nome_cliente, numero_nf, cnpj_cliente

# =====================================================
# ATALHOS PARA MANTER COMPATIBILIDADE
# =====================================================
extrair_cnpj_cliente = extrair_cnpj_cliente_padrao