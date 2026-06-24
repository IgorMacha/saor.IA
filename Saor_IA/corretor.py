import os
from pathlib import Path

import openai
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


PASTA_PROJETO = Path(__file__).resolve().parent
ARQUIVO_ENV = PASTA_PROJETO / ".env"

load_dotenv(
    dotenv_path=ARQUIVO_ENV,
    override=False,
)


def obter_configuracao(
    nome: str,
    padrao: str | None = None,
) -> str | None:
    """
    Procura configurações localmente e no Streamlit Cloud.
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


def corrigir_redacao(
    texto: str,
    tema: str = "",
    nivel: str = "Não informado",
) -> tuple[bool, str]:
    """
    Corrige uma redação escrita em inglês.

    A avaliação e as explicações são produzidas em português.
    """

    texto = texto.strip()
    tema_formatado = tema.strip() or "Não informado"
    nivel_formatado = nivel.strip() or "Não informado"

    if not texto:
        return False, "O texto da redação está vazio."

    if len(texto.split()) < 20:
        return (
            False,
            "O texto está muito curto para uma avaliação confiável.",
        )

    prompt = f"""
Você é um professor experiente de Língua Inglesa.

Avalie a redação em inglês apresentada abaixo.

O texto foi transcrito de uma imagem manuscrita. Portanto, alguns erros podem
ter sido causados pela leitura automática. Quando uma palavra ou frase parecer
estranha e houver possibilidade de erro de transcrição, informe essa incerteza.

DADOS:
- Tema: {tema_formatado}
- Nível do estudante: {nivel_formatado}

Use obrigatoriamente esta estrutura:

# Nota final: X/10

## Avaliação geral
Apresente um parágrafo curto, claro e pedagógico sobre a qualidade geral da
redação.

## Pontos positivos
Apresente os principais acertos relacionados a:
- desenvolvimento das ideias;
- organização;
- vocabulário;
- gramática;
- clareza.

## Pontos a melhorar
Avalie:
- adequação ao tema;
- introdução, desenvolvimento e conclusão;
- organização dos parágrafos;
- coerência e coesão;
- desenvolvimento dos argumentos;
- variedade e adequação do vocabulário;
- gramática da língua inglesa;
- ortografia;
- pontuação.

## Correções importantes
Apresente de 4 a 10 exemplos, quando existirem, usando exatamente este formato:

- Original: "frase original em inglês"
- Correção: "frase corrigida em inglês"
- Explicação: explicação em português

## Orientações práticas
Dê três recomendações específicas, em português, para o aluno melhorar a
próxima redação em inglês.

REGRAS:
- A nota deve estar entre 0 e 10.
- Todo o feedback deve ser escrito em português do Brasil.
- As frases originais e corrigidas devem permanecer em inglês.
- Não traduza a redação inteira.
- Não reescreva a redação inteira.
- Não invente conteúdo.
- Não penalize duas vezes o mesmo erro.
- Diferencie erros graves de pequenos deslizes.
- Seja respeitoso, claro, específico e pedagógico.
- Quando um possível erro puder ter sido causado pela transcrição da imagem,
  sinalize isso.

REDAÇÃO EM INGLÊS:
---
{texto}
---
"""

    try:
        cliente = obter_cliente()

        modelo = obter_configuracao(
            "OPENAI_MODEL",
            "gpt-4.1-mini",
        )

        resposta = cliente.responses.create(
            model=modelo,
            instructions=(
                "Analise a redação em inglês, mas produza todo o feedback "
                "em português do Brasil. Mantenha em inglês apenas os exemplos "
                "de frases originais e corrigidas."
            ),
            input=prompt,
            max_output_tokens=1800,
        )

        avaliacao = (
            resposta.output_text or ""
        ).strip()

        if not avaliacao:
            return (
                False,
                "A API processou a redação, mas não retornou uma avaliação.",
            )

        return True, avaliacao

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
            "Verifique sua conexão com a internet.",
        )

    except openai.BadRequestError as erro:
        return (
            False,
            f"A API recusou a solicitação: {erro}",
        )

    except openai.APIError as erro:
        return (
            False,
            f"Erro da API da OpenAI: {erro}",
        )

    except Exception as erro:
        return (
            False,
            f"Erro inesperado durante a correção: {erro}",
        )
