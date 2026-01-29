import os
import sys
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
    nome, cnpj, valor, vencimento = extrair_dados_cliente(texto)

    if not cnpj:
        LOG_ERROS.append(f"{arquivo} → CNPJ não encontrado no boleto")
        continue

    if not valor:
        LOG_ERROS.append(f"{arquivo} → Valor não encontrado no boleto")
        continue

    cnpj = limpar_cnpj(cnpj)
    vencimento = f"{datetime.now().month:02d}/{datetime.now().year}"

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
        LOG_ERROS.append(f"CNPJ {cnpj} → E-mail não encontrado")
        continue

    for email in emails:

        # 📄 ENVIAR NOTAS
        for nf in dados["nfs"]:
            if not ja_enviado(nf["arquivo"], cnpj, email):
                enviar_nota_fiscal(email, nf["caminho"], nf["numero_nf"], nf["nome"])
                registrar_envio(nf["arquivo"], cnpj, email)
                LOG_SUCESSO.append(f"NF {nf['numero_nf']} enviada para {email}")

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
                LOG_SUCESSO.append(f"Boleto {boleto['arquivo']} enviado para {email}")


# =========================================================
# 📊 RELATÓRIO FINAL
# =========================================================
print("\n✅ ENVIOS REALIZADOS:")
for s in LOG_SUCESSO:
    print("-", s)

if LOG_ERROS:
    print("\n❌ ERROS ENCONTRADOS:")
    for erro in LOG_ERROS:
        print("-", erro)
