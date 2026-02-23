# utils.py
import os
from datetime import datetime
import config

def get_mes_ano():
    """Retorna mês e ano das configurações ou atual"""
    try:
        return config.MES_REFERENCIA, config.ANO_REFERENCIA
    except:
        return datetime.now().strftime("%m"), datetime.now().strftime("%Y")

def get_assunto_email(tipo="boleto"):
    """Retorna assunto do email configurado"""
    mes, ano = get_mes_ano()
    try:
        if tipo == "boleto":
            return config.ASSUNTO_EMAIL.format(MES=mes, ANO=ano)
        else:
            return f"NOTA FISCAL REF. {mes}/{ano}"
    except:
        if tipo == "boleto":
            return f"BOLETO REFERENTE LOCAÇÃO MÊS {mes}/{ano}"
        else:
            return f"NOTA FISCAL REF. {mes}/{ano}"

def get_corpo_email(nome_cliente, valor=None, vencimento=None, numero_nf=None):
    """Retorna corpo do email configurado"""
    mes, ano = get_mes_ano()
    
    if numero_nf:  # É nota fiscal
        return f"""
Olá, {nome_cliente},

Segue em anexo a Nota Fiscal nº {numero_nf}
referente à locação do sistema — mês {mes}/{ano}.

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
    else:  # É boleto
        return f"""
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