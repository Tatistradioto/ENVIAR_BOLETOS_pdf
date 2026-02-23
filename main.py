import os
import sys
import re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

from buscar_email import buscar_email_por_cnpj
from enviar_email import enviar_boleto, enviar_nota_fiscal
from ler_pdf import extrair_texto_pdf, extrair_dados_cliente, extrair_dados_nf

ARQUIVO_CONTROLE = "controle_envios.txt"
PASTA_BOLETOS = "boletos"

LOG_ERROS = []
LOG_SUCESSO = []


def limpar_cnpj(cnpj):
    return ''.join(filter(str.isdigit, str(cnpj)))


def caminho_controle():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ARQUIVO_CONTROLE)


def ja_enviado(arquivo, cnpj, email):
    caminho = caminho_controle()
    if not os.path.exists(caminho):
        return False
    with open(caminho, "r", encoding="utf-8") as f:
        registros = f.read().splitlines()
    return f"{arquivo}|{cnpj}|{email}" in registros


def registrar_envio(arquivo, cnpj, email):
    caminho = caminho_controle()
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(f"{arquivo}|{cnpj}|{email}\n")


documentos_por_cnpj = {}

# =========================================================
# 1️⃣ AGRUPAR DOCUMENTOS
# =========================================================
for arquivo in os.listdir(PASTA_BOLETOS):

    if not arquivo.lower().endswith(".pdf"):
        continue

    caminho_pdf = os.path.join(PASTA_BOLETOS, arquivo)
    texto = extrair_texto_pdf(caminho_pdf)

    # -------- NOTA FISCAL --------
    if "DADOS DO TOMADOR DE SERVIÇOS" in texto:

        nome_nf, numero_nf, cnpj_nf = extrair_dados_nf(texto)

        if not cnpj_nf:
            LOG_ERROS.append(f"{arquivo} → CNPJ NF não encontrado")
            continue

        cnpj_nf = limpar_cnpj(cnpj_nf)

        documentos_por_cnpj.setdefault(cnpj_nf, {"boletos": [], "nfs": []})

        documentos_por_cnpj[cnpj_nf]["nfs"].append({
            "arquivo": arquivo,
            "caminho": caminho_pdf,
            "nome": nome_nf,
            "numero_nf": numero_nf
        })

        continue

    # -------- BOLETOS --------
    # Extrai dados do boleto usando as funções melhoradas
    nome, cnpj, valor, vencimento = extrair_dados_cliente(texto)
    
    # Debug - mostra o que foi extraído
    print(f"\n📄 Processando: {arquivo}")
    print(f"   Nome: {nome}")
    print(f"   CNPJ: {cnpj}")
    print(f"   Valor: {valor}")
    print(f"   Vencimento: {vencimento}")

    if not cnpj:
        # Tenta extrair CNPJ diretamente do PDF
        from extrair_cnpj import extrair_cnpj_cliente as extrair_cnpj_direto
        cnpj = extrair_cnpj_direto(caminho_pdf)
        print(f"   CNPJ (extração direta): {cnpj}")

    if not cnpj:
        LOG_ERROS.append(f"{arquivo} → CNPJ não encontrado no boleto")
        continue

    if not valor:
        LOG_ERROS.append(f"{arquivo} → Valor não encontrado no boleto")
        # Tenta extrair valor com método alternativo
        match_valor = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
        if match_valor:
            valor = match_valor.group(1).replace(".", "").replace(",", ".")
            print(f"   Valor (método alternativo): {valor}")

    if not vencimento:
        vencimento = f"{datetime.now().day:02d}/{datetime.now().month:02d}/{datetime.now().year}"
        print(f"   Vencimento (gerado): {vencimento}")

    cnpj = limpar_cnpj(cnpj)

    # Se não tem nome, usa um placeholder
    if not nome or nome == "None":
        nome = "Cliente"
        # Tenta extrair nome do nome do arquivo
        nome_arquivo = arquivo.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        if len(nome_arquivo) > 5 and not re.search(r'\d{4,}', nome_arquivo):
            nome = nome_arquivo[:50]
            print(f"   Nome (do arquivo): {nome}")

    documentos_por_cnpj.setdefault(cnpj, {"boletos": [], "nfs": []})

    documentos_por_cnpj[cnpj]["boletos"].append({
        "arquivo": arquivo,
        "caminho": caminho_pdf,
        "nome": nome,
        "valor": valor,
        "vencimento": vencimento
    })
    
# =========================================================
# 2️⃣ ENVIAR AGRUPADO
# =========================================================
for cnpj, dados in documentos_por_cnpj.items():

    emails = buscar_email_por_cnpj(cnpj)

    if not emails:
        # Pega o nome do primeiro boleto ou NF deste CNPJ
        nome_cliente = "Desconhecido"
        if dados["boletos"]:
            nome_cliente = dados["boletos"][0]["nome"]
        elif dados["nfs"]:
            nome_cliente = dados["nfs"][0]["nome"]
        
        LOG_ERROS.append(f"❌ CNPJ {cnpj} - {nome_cliente} → E-mail não encontrado")
        continue

    for email in emails:
        print(f"\n📧 Processando envios para: {email}")

        # 📄 ENVIAR NOTAS
        for nf in dados["nfs"]:
            if not ja_enviado(nf["arquivo"], cnpj, email):
                enviar_nota_fiscal(
                    email,
                    nf["caminho"],
                    nf["nome"],
                    nf["numero_nf"]
                )
                registrar_envio(nf["arquivo"], cnpj, email)
                LOG_SUCESSO.append(f"✅ NF {nf['numero_nf']} - {nf['nome']} enviada para {email}")
                print(f"   ✅ NF enviada: {nf['numero_nf']} - {nf['nome']}")
            else:
                print(f"   ⏭️ NF já enviada: {nf['numero_nf']} - {nf['nome']} (duplicado)")
                LOG_SUCESSO.append(f"⏭️ NF {nf['numero_nf']} - {nf['nome']} já enviada para {email} (duplicado)")

        # 💰 ENVIAR BOLETOS
        for boleto in dados["boletos"]:
            if not ja_enviado(boleto["arquivo"], cnpj, email):
                enviar_boleto(
                    email,
                    boleto["caminho"],
                    boleto["nome"],
                    boleto["valor"],
                    boleto["vencimento"]
                )
                registrar_envio(boleto["arquivo"], cnpj, email)
                LOG_SUCESSO.append(f"✅ Boleto {boleto['arquivo']} - {boleto['nome']} enviado para {email}")
                print(f"   ✅ Boleto enviado: {boleto['nome']}")
            else:
                print(f"   ⏭️ Boleto já enviado: {boleto['nome']} (duplicado)")
                LOG_SUCESSO.append(f"⏭️ Boleto {boleto['arquivo']} - {boleto['nome']} já enviado para {email} (duplicado)")


# =========================================================
# 📊 RELATÓRIO FINAL
# =========================================================
print("\n" + "=" * 60)
print("📊 RESUMO DOS ENVIOS")
print("=" * 60)

if LOG_SUCESSO:
    print("\n📤 DOCUMENTOS PROCESSADOS:")
    for item in LOG_SUCESSO:
        print(f"  {item}")
else:
    print("\n📭 Nenhum documento novo para enviar.")
    print("   Todos os documentos já foram enviados anteriormente!")

if LOG_ERROS:
    print("\n❌ ERROS ENCONTRADOS:")
    for erro in LOG_ERROS:
        print(f"  {erro}")

print("\n💡 Dica: Para reenviar um documento, apague a linha correspondente em controle_envios.txt")
print("=" * 60)