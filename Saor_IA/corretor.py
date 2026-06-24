import os

import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _obter_cliente() -> OpenAI:
    chave = os.getenv("OPENAI_API_KEY")

    if not chave:
        raise ValueError(
            "A variável OPENAI_API_KEY não foi configurada. "
            "Adicione sua chave no arquivo .env."
        )

    return OpenAI(api_key=chave)


def corrigir_redacao(
    texto: str,
    tema: str = "",
    nivel: str = "Não informado",
) -> tuple[bool, str]:
    """
    Avalia a redação e retorna (sucesso, conteúdo).
    """
    tema_formatado = tema.strip() or "Não informado"

    instrucoes = f"""
Você é um professor de Língua Portuguesa responsável por corrigir redações.

Avalie exclusivamente o texto apresentado. Não invente trechos e considere que
alguns erros pequenos podem ter sido causados pela transcrição automática da
imagem.

Dados:
- Tema: {tema_formatado}
- Nível de ensino: {nivel}

Use obrigatoriamente esta estrutura:

# Nota final: X/10

## Resumo da avaliação
Um parágrafo curto e claro.

## Pontos positivos
Liste os principais acertos.

## Pontos a melhorar
Analise:
- adequação ao tema;
- estrutura e organização;
- coerência e coesão;
- argumentação;
- gramática, ortografia e pontuação.

## Correções importantes
Mostre exemplos no formato:
- Trecho identificado → sugestão corrigida → breve explicação.

## Orientação prática
Dê três ações objetivas para melhorar a próxima redação.

Regras:
- A nota deve estar entre 0 e 10.
- Seja respeitoso, pedagógico e específico.
- Não reescreva integralmente a redação.
- Quando houver dúvida causada pelo OCR, sinalize essa incerteza.

REDAÇÃO:
---
{texto.strip()}
---
"""

    try:
        cliente = _obter_cliente()
        modelo = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

        resposta = cliente.responses.create(
            model=modelo,
            instructions=(
                "Responda em português do Brasil. Produza uma avaliação "
                "pedagógica, criteriosa e objetiva."
            ),
            input=instrucoes,
            max_output_tokens=1000,
        )

        avaliacao = resposta.output_text.strip()

        if not avaliacao:
            return False, "A API respondeu sem conteúdo. Tente novamente."

        return True, avaliacao

    except ValueError as erro:
        return False, str(erro)

    except openai.AuthenticationError:
        return (
            False,
            "A chave da OpenAI é inválida, expirou ou foi revogada. "
            "Gere outra chave e atualize o arquivo .env.",
        )

    except openai.RateLimitError as erro:
        mensagem = str(erro).lower()
        if "insufficient_quota" in mensagem or "current quota" in mensagem:
            return (
                False,
                "Sua conta da API está sem crédito ou atingiu o limite de gastos. "
                "Confira Billing e Usage na OpenAI Platform.",
            )
        return (
            False,
            "O limite temporário de requisições foi atingido. Tente novamente "
            "daqui a pouco.",
        )

    except openai.APIConnectionError:
        return (
            False,
            "Não foi possível conectar à OpenAI. Confira sua internet, VPN, "
            "proxy ou firewall.",
        )

    except openai.BadRequestError as erro:
        return False, f"A API recusou a solicitação: {erro}"

    except openai.APIError as erro:
        return False, f"Erro da API da OpenAI: {erro}"

    except Exception as erro:
        return False, f"Erro inesperado durante a correção: {erro}"
