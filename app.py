import os
import subprocess
import streamlit as st


st.set_page_config(page_title="Envio de Boletos", layout="centered")

st.markdown("<h1 style='color:#FF7A00; text-align:center;'>📧 Sistema de Envio de Boletos</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Automação de envio de boletos e notas fiscais</p>", unsafe_allow_html=True)

st.divider()

# 📂 UPLOAD DE PDFs
st.subheader("📂 Enviar novos PDFs")

arquivos = st.file_uploader(
    "Arraste ou selecione boletos e notas fiscais",
    type=["pdf"],
    accept_multiple_files=True
)

if arquivos:
    os.makedirs("boletos", exist_ok=True)

    for arquivo in arquivos:
        caminho = os.path.join("boletos", arquivo.name)
        with open(caminho, "wb") as f:
            f.write(arquivo.getbuffer())

    st.success("Arquivos enviados para a pasta boletos com sucesso!")

st.divider()

# 🚀 EXECUÇÃO DO SISTEMA
st.subheader("🚀 Executar sistema")
st.write("Clique no botão para iniciar o envio dos documentos da pasta **boletos**.")

if st.button("🧡 Executar envio"):
    st.info("Processando... Aguarde.")

    try:
        resultado = subprocess.run(
            ["python", "main.py"],
            capture_output=True,
            encoding="utf-8",
            errors="ignore"
        )

        if resultado.returncode == 0:
            st.success("✅ Processo finalizado com sucesso!")
            st.text(resultado.stdout)
        else:
            st.error("❌ Ocorreu um erro.")
            st.text(resultado.stderr)

    except Exception as e:
        st.error(f"Erro ao executar: {e}")

st.divider()

st.markdown(
    "<p style='text-align:center; color:gray;'>Desenvolvido por Tatiana Stradioto</p>",
    unsafe_allow_html=True
)
