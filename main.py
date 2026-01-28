import os
from buscar_email import buscar_email_por_cnpj
from enviar_email import enviar_boleto, enviar_nota_fiscal
from ler_pdf import extrair_texto_pdf, extrair_dados_cliente, extrair_dados_nf

ARQUIVO_CONTROLE = "controle_envios.txt"


def ja_enviado(arquivo, cnpj, email):
    if not os.path.exists(ARQUIVO_CONTROLE):
        return False

    with open(ARQUIVO_CONTROLE, "r", encoding="utf-8") as f:
        registros = f.read().splitlines()

    chave = f"{arquivo}|{cnpj}|{email}"
    return chave in registros


def registrar_envio(arquivo, cnpj, email):
    with open(ARQUIVO_CONTROLE, "a", encoding="utf-8") as f:
        f.write(f"{arquivo}|{cnpj}|{email}\n")


PASTA_BOLETOS = "boletos"
falhas_envio = []

print("\n🚀 Sistema de envio de documentos iniciado\n")

for arquivo in os.listdir(PASTA_BOLETOS):

    if not arquivo.lower().endswith(".pdf"):
        continue

    caminho_pdf = os.path.join(PASTA_BOLETOS, arquivo)

    print("=" * 70)
    print(f"📄 Lendo arquivo: {arquivo}")

    texto = extrair_texto_pdf(caminho_pdf)

    # =========================================================
    # 🔥 1️⃣ SE FOR NOTA FISCAL
    # =========================================================
    if "DADOS DO TOMADOR DE SERVIÇOS" in texto:

        print("🧾 Documento identificado como NOTA FISCAL")

        nome_nf, numero_nf, cnpj_nf = extrair_dados_nf(texto)

        print(f"👤 Cliente NF: {nome_nf}")
        print(f"🔢 Número NF: {numero_nf}")
        print(f"🧾 CNPJ NF: {cnpj_nf}")

        if not cnpj_nf:
            print("❌ CNPJ do tomador não encontrado\n")
            falhas_envio.append((arquivo, "CNPJ NF não encontrado"))
            continue

        emails = buscar_email_por_cnpj(cnpj_nf)
        print(f"📧 E-mails encontrados: {emails}")

        if not emails:
            print("❌ E-mail não encontrado\n")
            falhas_envio.append((arquivo, "E-mail NF não encontrado"))
            continue

        for email in emails:

            # 🔒 BLOQUEIO DUPLICIDADE
            if ja_enviado(arquivo, cnpj_nf, email):
                print("⛔ NF já enviada para esse CNPJ e e-mail. Pulando.")
                continue

            try:
                print(f"📤 Enviando NF para: {email}")
                enviar_nota_fiscal(email, caminho_pdf, nome_nf, numero_nf)
                print("✅ Nota fiscal enviada com sucesso!")
                registrar_envio(arquivo, cnpj_nf, email)

            except Exception as e:
                print(f"❌ Erro ao enviar NF para {email}: {e}")
                falhas_envio.append((arquivo, email))

        print()
        continue

    # =========================================================
    # 💳 2️⃣ FLUXO NORMAL DE BOLETOS (INALTERADO)
    # =========================================================
    nome, cnpj, valor, vencimento = extrair_dados_cliente(texto)

    print(f"👤 Cliente: {nome}")
    print(f"🧾 CNPJ cliente: {cnpj}")
    print(f"💰 Valor: {valor}")
    print(f"📅 Vencimento: {vencimento}")

    if not cnpj:
        print("❌ CNPJ do cliente não encontrado\n")
        falhas_envio.append((arquivo, "CNPJ não encontrado"))
        continue

    emails = buscar_email_por_cnpj(cnpj)
    print(f"📧 E-mails encontrados: {emails}")

    if not emails:
        print("❌ E-mail não encontrado\n")
        falhas_envio.append((arquivo, "E-mail não encontrado"))
        continue

    eh_inter = "AUTENTICAÇÃO MECÂNICA" in texto or "CÓDIGO BENEFICIÁRIO" in texto

    if eh_inter:
        print("🏦 Boleto identificado como Banco Inter")
        if not valor:
            print("❌ Valor não encontrado no boleto\n")
            falhas_envio.append((arquivo, "Valor não encontrado"))
            continue
    else:
        if not valor or not vencimento:
            print("❌ Valor ou vencimento não encontrados no boleto\n")
            falhas_envio.append((arquivo, "Valor/Vencimento ausente"))
            continue

    # 🚀 ENVIO DE BOLETO
    for email in emails:

        # 🔒 BLOQUEIO DUPLICIDADE
        if ja_enviado(arquivo, cnpj, email):
            print("⛔ Boleto já enviado para esse CNPJ e e-mail. Pulando.")
            continue

        try:
            print(f"📤 Enviando boleto para: {email}")
            enviar_boleto(email, caminho_pdf, nome, valor, vencimento)
            print("✅ Boleto enviado com sucesso!")
            registrar_envio(arquivo, cnpj, email)

        except Exception as e:
            print(f"❌ Erro ao enviar boleto para {email}: {e}")
            falhas_envio.append((arquivo, email))

    print()

# =========================================================
print("=" * 70)
print("🏁 Processo finalizado.\n")

if falhas_envio:
    print("⚠️ DOCUMENTOS NÃO ENVIADOS:")
    for falha in falhas_envio:
        print(f" • Documento: {falha[0]}  |  Motivo/E-mail: {falha[1]}")
else:
    print("🎉 Todos os documentos foram enviados com sucesso!")
