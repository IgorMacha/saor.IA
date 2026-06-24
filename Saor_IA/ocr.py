import base64
import io
import os
from pathlib import Path

import openai
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageEnhance, ImageOps


PASTA_PROJETO = Path(__file__).resolve().parent
ARQUIVO_ENV = PASTA_PROJETO / ".env"

# Carrega o .env somente quando ele existir localmente.
load_dotenv(
    dotenv_path=ARQUIVO_ENV,
    override=False,
)


def obter_configuracao(
    nome: str,
    padrao: str | None = None,
) -> str | None:
    """
    Procura uma configuração nesta ordem:

    1. variável de ambiente;
    2. arquivo .env local;
    3. Secrets do Streamlit Cloud;
    4. valor padrão.
    """

    valor = os.getenv(nome)

    if valor:
        return valor.strip()

    try:
        if nome in st.secrets:
            valor_secret = st.secrets[nome]

            if valor_secret:
                return str(valor_secret).strip()
    except Exception:
        pass

    return padrao


def obter_cliente() -> OpenAI:
    """
    Cria o cliente da OpenAI.
    """

    chave = obter_configuracao("OPENAI_API_KEY")

    if not chave:
        raise ValueError(
            "OPENAI_API_KEY não encontrada. "
            "No computador, configure o arquivo .env. "
            "No Streamlit Cloud, configure em Manage app > Settings > Secrets."
        )

    return OpenAI(api_key=chave)


def preparar_imagem(imagem: Image.Image) -> Image.Image:
    """
    Ajusta orientação, tamanho, contraste e nitidez da imagem.
    """

    imagem = ImageOps.exif_transpose(imagem)
    imagem = imagem.convert("RGB")

    largura, altura = imagem.size
    maior_lado = max(largura, altura)

    # Evita imagens excessivamente grandes.
    if maior_lado > 3000:
        proporcao = 3000 / maior_lado

        nova_largura = int(largura * proporcao)
        nova_altura = int(altura * proporcao)

        imagem = imagem.resize(
            (nova_largura, nova_altura),
            Image.Resampling.LANCZOS,
        )

    # Pequenos ajustes preservam a escrita original.
    imagem = ImageEnhance.Contrast(imagem).enhance(1.12)
    imagem = ImageEnhance.Sharpness(imagem).enhance(1.18)

    return imagem


def imagem_para_base64(imagem: Image.Image) -> str:
    """
    Converte a imagem para uma URL Base64.
    """

    buffer = io.BytesIO()

    imagem.save(
        buffer,
        format="JPEG",
        quality=95,
        optimize=True,
    )

    conteudo_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return f"data:image/jpeg;base64,{conteudo_base64}"


def limpar_resposta(texto: str) -> str:
    """
    Remove possíveis blocos Markdown adicionados pelo modelo.
    """

    texto = texto.strip()

    if texto.startswith("```"):
        linhas = texto.splitlines()

        if linhas:
            linhas = linhas[1:]

        if linhas and linhas[-1].strip() == "```":
            linhas = linhas[:-1]

        texto = "\n".join(linhas).strip()

    return texto


def extrair_texto(
    imagem: Image.Image,
) -> tuple[bool, str]:
    """
    Transcreve uma redação manuscrita em inglês.

    Retorna:
        (True, transcrição)
        (False, mensagem de erro)
    """

    try:
        cliente = obter_cliente()

        imagem_processada = preparar_imagem(imagem)
        imagem_base64 = imagem_para_base64(imagem_processada)

        modelo = obter_configuracao(
            "OPENAI_VISION_MODEL",
            "gpt-4.1-mini",
        )

        resposta = cliente.responses.create(
            model=modelo,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": """
Você é um especialista em transcrição de textos manuscritos.

Transcreva fielmente a redação manuscrita em inglês presente na imagem.

Regras obrigatórias:
- Retorne somente a transcrição.
- Preserve o idioma inglês.
- Preserve os parágrafos.
- Não traduza.
- Não corrija gramática, ortografia ou pontuação.
- Não reescreva o texto para deixá-lo melhor.
- Não invente palavras ou frases.
- Ignore nome do aluno, escola, turma, data, número da página e instruções impressas.
- Inclua o título da redação, caso exista.
- Quando uma palavra estiver realmente ilegível, escreva [ilegível].
- Quando uma frase estiver cortada no final da imagem, transcreva somente a parte visível.
""",
                        },
                        {
                            "type": "input_image",
                            "image_url": imagem_base64,
                            "detail": "high",
                        },
                    ],
                }
            ],
            max_output_tokens=3000,
        )

        texto = limpar_resposta(
            resposta.output_text or ""
        )

        if not texto:
            return (
                False,
                "A imagem foi processada, mas nenhum texto foi identificado.",
            )

        quantidade_palavras = len(texto.split())

        if quantidade_palavras < 10:
            return (
                False,
                "Pouco texto foi identificado. Envie uma foto mais nítida, "
                "reta, sem sombras e com a folha inteira visível.",
            )

        return True, texto

    except ValueError as erro:
        return False, str(erro)

    except openai.AuthenticationError:
        return (
            False,
            "A chave da OpenAI é inválida, foi revogada ou está incorreta.",
        )

    except openai.RateLimitError as erro:
        mensagem = str(erro).lower()

        if (
            "insufficient_quota" in mensagem
            or "current quota" in mensagem
        ):
            return (
                False,
                "A conta da API está sem crédito ou atingiu o limite de gastos.",
            )

        return (
            False,
            "O limite temporário de requisições foi atingido. "
            "Tente novamente em alguns instantes.",
        )

    except openai.APIConnectionError:
        return (
            False,
            "Não foi possível conectar à OpenAI. "
            "Verifique a internet, VPN, proxy ou firewall.",
        )

    except openai.BadRequestError as erro:
        return (
            False,
            f"A API recusou a imagem ou a solicitação: {erro}",
        )

    except openai.APIError as erro:
        return (
            False,
            f"Erro da API da OpenAI: {erro}",
        )

    except Exception as erro:
        return (
            False,
            f"Erro inesperado ao transcrever a imagem: {erro}",
        )
