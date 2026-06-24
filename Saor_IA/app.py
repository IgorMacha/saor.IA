import streamlit as st
from PIL import Image

from ocr import extrair_texto
from corretor import corrigir_redacao

st.set_page_config(
    page_title="saor.IA",
    page_icon="📝",
    layout="centered",
)

st.title("📝 saor.IA")
st.caption("Envie uma foto de uma redação manuscrita para transcrever, avaliar e receber comentários.")

with st.sidebar:
    st.header("Critérios")
    tema = st.text_input("Tema da redação (opcional)")
    nivel = st.selectbox(
        "Nível de ensino",
        ["Não informado", "Ensino Fundamental", "Ensino Médio", "Ensino Superior"],
    )
    st.info(
        "Para melhorar a leitura: fotografe a folha de frente, com boa iluminação "
        "e sem sombras."
    )

arquivo = st.file_uploader(
    "Selecione a foto da redação",
    type=["png", "jpg", "jpeg"],
)

if arquivo is not None:
    imagem = Image.open(arquivo).convert("RGB")
    st.image(imagem, caption="Imagem enviada", use_container_width=True)

    if st.button("Ler redação", type="primary", use_container_width=True):
        with st.spinner("Lendo o texto da imagem..."):
            sucesso, resultado_ocr = extrair_texto(imagem)

        if sucesso:
            st.session_state["texto_redacao"] = resultado_ocr
            st.success("Texto extraído. Revise antes de solicitar a correção.")
        else:
            st.error(resultado_ocr)

if "texto_redacao" in st.session_state:
    texto_editado = st.text_area(
        "Texto extraído — você pode corrigir erros do OCR",
        value=st.session_state["texto_redacao"],
        height=320,
    )

    if st.button("Corrigir redação", use_container_width=True):
        if len(texto_editado.strip()) < 40:
            st.warning("O texto está muito curto para uma avaliação confiável.")
        else:
            with st.spinner("Avaliando a redação..."):
                sucesso, avaliacao = corrigir_redacao(
                    texto=texto_editado,
                    tema=tema,
                    nivel=nivel,
                )

            if sucesso:
                st.subheader("Avaliação")
                st.markdown(avaliacao)
                st.download_button(
                    "Baixar avaliação em TXT",
                    data=avaliacao,
                    file_name="avaliacao_saor_ia.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            else:
                st.error(avaliacao)
