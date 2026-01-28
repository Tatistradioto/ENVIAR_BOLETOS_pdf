# 📧 Sistema de Envio Automático de Boletos e Notas Fiscais

Sistema desenvolvido em Python para automatizar o envio de boletos e notas fiscais em PDF por e-mail, com leitura automática de dados dos documentos.

---

## 🚀 Funcionalidades

✔ Leitura automática de PDFs  
✔ Extração de CNPJ do cliente  
✔ Busca automática de e-mails nos contatos Google  
✔ Envio de boletos por e-mail  
✔ Envio de notas fiscais por e-mail  
✔ Controle de documentos já enviados  
✔ Integração com Gmail API  

---

## 🧠 Tecnologias utilizadas

- Python
- Google Gmail API
- Google People API
- PDFPlumber
- Git & GitHub

---

## 🔐 Segurança

O sistema utiliza autenticação OAuth do Google.  
Credenciais e tokens são mantidos localmente e não fazem parte do repositório.

---

## ▶️ Como executar

1. Instalar dependências:

pip install pdfplumber google-auth google-auth-oauthlib google-api-python-client   

2. Colocar os PDFs na pasta `boletos`

3. Executar:

python main.py

---

## 👩‍💻 Autora

Tatiana Stradioto  
Sistema desenvolvido para automação de processos financeiros.
