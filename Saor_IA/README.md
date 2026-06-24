# saor.IA

Aplicação em Streamlit para:

1. receber uma foto de redação manuscrita;
2. extrair o texto com Tesseract OCR;
3. permitir a revisão da transcrição;
4. avaliar a redação de 0 a 10 com a OpenAI;
5. gerar comentários e um arquivo TXT.

## 1. Instalar o Tesseract OCR

No Windows, instale o Tesseract e confirme se existe:

`C:\Program Files\Tesseract-OCR\tesseract.exe`

Para português, confirme também:

`C:\Program Files\Tesseract-OCR\tessdata\por.traineddata`

## 2. Instalar as bibliotecas

Abra o terminal nesta pasta e execute:

```bat
python -m pip install -r requirements.txt
```

Ou dê dois cliques em `instalar.bat`.

## 3. Configurar a chave da OpenAI

1. Copie `.env.example`.
2. Renomeie a cópia para `.env`.
3. Abra `.env` no Bloco de Notas.
4. Troque `cole_sua_chave_aqui` pela chave verdadeira.
5. Salve o arquivo.

Exemplo:

```text
OPENAI_API_KEY=sk-proj-xxxxxxxx
```

Nunca envie o arquivo `.env` para outra pessoa e não publique a chave no GitHub.

## 4. Rodar

No terminal:

```bat
python -m streamlit run app.py
```

Ou dê dois cliques em `executar.bat`.

O navegador deve abrir em:

`http://localhost:8501`

## Erros comuns

- `TesseractNotFoundError`: Tesseract não instalado ou caminho incorreto.
- `401 invalid_api_key`: chave incorreta.
- `429 insufficient_quota`: conta da API sem crédito ou limite de gastos atingido.
- `Failed loading language por`: arquivo `por.traineddata` ausente.
