# Gandalf

Para executar o build de produção com Nginx, API e PostgreSQL juntos, consulte a [receita de integração](docs/deployment-integration.md). O caminho é opt-in e preserva o iniciador local com SQLite; as configurações e os limites do teste estão documentados nessa receita.

> **Estado atual (2026-09-29):** o guia abaixo descreve o modo local. Existe também um modo online experimental com MusicBrainz, Open Library e Groq opcional. Leia o [estado da implementação](docs/IMPLEMENTATION_STATUS.md) para distinguir recursos atuais, limites e funcionalidades planejadas. A [avaliação local](docs/eval-reports/2026-09-29-local-baseline.md) cobre 45 consultas, com baselines em K=5 e K=10.

Para ativar explicitamente o modo online, use `./start-local.ps1 -Online`. A configuração opcional da IA fica em `api/.env` a partir de `api/.env.example`; não exponha a chave no frontend. O limite diário interno controla tentativas de chamadas, não faturamento. Sem `-Online`, o iniciador mantém o caminho local sem chamadas externas.

Descubra m?sicas e livros pelo que voc? quer sentir e monte uma sele??o musical para acompanhar sua leitura.

O modo local funciona **sem chave de API, assinatura, Docker ou servi?o pago**. Depois de instalar as depend?ncias, as buscas e recomenda??es funcionam sem internet. Os links para ouvir m?sicas e consultar livros precisam de conex?o.

## Executar no Windows

Requisitos: Python 3.12+ e Node.js com npm. Na raiz do projeto:

```powershell
# Primeira execu??o: instala depend?ncias gratuitas
.\start-local.ps1 -Install

# Execu??es seguintes
.\start-local.ps1
```

Abra **http://127.0.0.1:5173**. API: http://127.0.0.1:8000. Swagger: http://127.0.0.1:8000/docs. Ctrl+C encerra a execu??o. Se alguma porta estiver ocupada, o script informa o conflito sem encerrar processos existentes.

O script inicia a API, migra automaticamente um SQLite local e inicia a interface. Contas, cat?logo consultado e cache ficam em `api/.local/gandalf.db`; o segredo de autentica??o ? gerado uma vez em `api/.local/jwt-secret`. Essa pasta ? ignorada pelo Git. Nenhum `.env` ? necess?rio: o iniciador local isola o banco/provider de configura??es externas.

Para executar separadamente, inclusive em outros sistemas:

```sh
cd api
python -m venv .venv
# Ative .venv conforme seu sistema
python -m pip install -e '.[dev]'
python local.py
```

Em outro terminal:

```sh
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

## Dispon?vel

- Descoberta p?blica por temas em portugu?s, refer?ncias a t?tulos do cat?logo e exclus?es simples, como ?fantasia sem romance?.
- Filtros de m?sica instrumental/com voz e energia baixa, m?dia ou alta.
- Busca de livro e sele??o musical nos modos Foco, Imersiva, Cinematogr?fica, Calma e Do seu jeito.
- Explica??o de cada sugest?o baseada nos crit?rios efetivamente usados.
- Links de busca no YouTube e na Open Library, temas claro/escuro e interface responsiva.
- API de cadastro, login, refresh rotativo e logout; os fluxos p?blicos n?o exigem conta.

Experimente ?Fantasia com constru??o de mundo?, ?M?sicas calmas para estudar?, ?Parecidas com No Surprises, mas instrumentais? ou selecione ?Duna? em **Ler com m?sica**.

## Limites atuais

O cat?logo inicial ? editorial: **18 livros e 25 m?sicas**. O ranking usa regras e temas; n?o usa LLM nem embeddings. Pedidos fora da cobertura podem retornar vazio. As classifica??es s?o subjetivas e a interpreta??o de frases complexas ? limitada.

N?o h? reprodu??o integrada nem exporta??o de playlists. A trilha ? uma lista de links de busca com estimativa de cinco minutos por faixa, n?o uma dura??o verificada de grava??o. A interface avisa quando o cat?logo n?o preenche a dura??o desejada. ?Poucos vocais? seleciona instrumentais conservadoramente.

Explica??es an?nimas ficam em mem?ria por at? uma hora, no m?ximo 256 buscas por processo, e expiram ao reiniciar. Hist?rico pessoal, feedback, itens salvos e telas de conta ainda n?o est?o dispon?veis. N?o houve deploy p?blico; a configura??o ? para uso local.

## Testes

```powershell
cd api
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app local.py alembic tests
.\.venv\Scripts\python.exe -m ruff format --check app local.py alembic tests
cd ../frontend
npm test
npm run build
```

`npm test` executa smoke tests e um E2E com FastAPI real e SQLite tempor?rio. O E2E usa `api/.venv` (ou `GANDALF_PYTHON`) e Chromium do Playwright. Se o navegador n?o estiver instalado: `npx playwright install chromium`. Nenhum teste usa servi?os pagos.

## Estrutura e evolu??o

| Caminho | Conte?do |
|---|---|
| `api/` | FastAPI, SQLAlchemy, autentica??o, providers e ranking local |
| `frontend/` | React, TypeScript, Vite e testes Playwright |
| `start-local.ps1` | Inicializa??o Windows |
| `docs/DEVELOPMENT_LOG.md` | Estado atual e pr?ximos passos |
| `docs/` | Especifica??es da arquitetura completa e roadmap |

Leia o [guia da API](api/README.md), o [registro de desenvolvimento](docs/DEVELOPMENT_LOG.md) e a [decis?o sobre o modo gratuito](docs/adr/0013-free-local-mode.md). As especifica??es descrevem tamb?m funcionalidades futuras, como providers musicais externos, embeddings e personaliza??o.
