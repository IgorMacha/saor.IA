import base64
import io
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageEnhance, ImageOps


PASTA_PROJETO = Path(__file__).resolve().parent
ARQUIVO_ENV = PASTA_PROJETO / ".env"

load_dotenv(dotenv_path=ARQUIVO_ENV, override=True)


def obter_cliente() -> OpenAI:
    chave = os.getenv("OPENAI_API_KEY")

    if not chave:
        raise ValueError(
            f"OPENAI_API_KEY não encontrada. Verifique o arquivo: {ARQUIVO_ENV}"
        )

    return OpenAI(api_key=chave)


def preparar_imagem(imagem: Image.Image) -> Image.Image:
    """
    Corrige a orientação, melhora o contraste e reduz imagens muito grandes.
    """

    imagem = ImageOps.exif_transpose(imagem)
    imagem = imagem.convert("RGB")

    largura, altura = imagem.size
    maior_lado = max(largura, altura)

    if maior_lado > 2400:
        proporcao = 2400 / maior_lado
        imagem = imagem.resize(
            (
                int(largura * proporcao),
                int(altura * proporcao),
            ),
            Image.Resampling.LANCZOS,
        )

    imagem = ImageEnhance.Contrast(imagem).enhance(1.15)
    imagem = ImageEnhance.Sharpness(imagem).enhance(1.25)

    return imagem


def imagem_para_base64(imagem: Image.Image) -> str:
    """
    Converte a imagem para uma URL Base64 aceita pela API.
    """

    buffer = io.BytesIO()

    imagem.save(
        buffer,
        format="JPEG",
        quality=95,
        optimize=True,
    )

    imagem_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return f"data:image/jpeg;base64,{imagem_base64}"


def extrair_texto(imagem: Image.Image) -> tuple[bool, str]:
    """
    Transcreve uma redação manuscrita em inglês usando visão.

    Retorna:
        (True, texto transcrito)
        (False, mensagem de erro)
    """

    try:
        cliente = obter_cliente()
        imagem_processada = preparar_imagem(imagem)
        imagem_base64 = imagem_para_base64(imagem_processada)

        resposta = cliente.responses.create(
            model=os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini"),
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": """
Transcreva fielmente esta redação manuscrita em inglês.

Regras:
- Transcreva apenas o conteúdo da redação.
- Ignore nome, escola, data, número da página e títulos administrativos.
- Preserve os parágrafos.
- Não corrija gramática, ortografia ou pontuação.
- Não complete frases que não estejam visíveis.
- Quando uma palavra estiver ilegível, escreva [ilegível].
- Não traduza o texto.
- Não faça comentários.
- Retorne somente a transcrição.
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
            max_output_tokens=2500,
        )

        texto = resposta.output_text.strip()

        if not texto:
            return (
                False,
                "A imagem foi processada, mas nenhum texto foi identificado.",
            )

        if len(texto.split()) < 10:
            return (
                False,
                "Pouco texto foi identificado. Tente enviar uma foto mais nítida, "
                "reta e com melhor iluminação.",
            )

        return True, texto

    except ValueError as erro:
        return False, str(erro)

    except Exception as erro:
        return False, f"Erro ao transcrever a imagem: {erro}"