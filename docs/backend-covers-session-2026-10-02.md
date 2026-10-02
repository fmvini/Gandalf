# Backend — capas de livros, 2026-10-02

## Implementado

- Diagnóstico read-only da API 8000, normalizador Open Library, edições portuguesas e URLs de capa, coordenado por Maestri com Frontend/Banco/Maestro. Core de favoritos/re-roll permaneceu congelado enquanto Maestro validou e serializou commits.
- Após autorização específica do Maestro, correção isolada: `cover_i` de edição portuguesa só substitui a capa da obra quando é inteiro estrito positivo. Valores 0/-1/bool/ausentes/inválidos conservam a capa válida da obra; se ambas são inválidas, `cover_url=null`.
- URLs novas mantêm HTTPS, Cover ID e tamanho M, acrescentando `?default=false`. A [documentação oficial Open Library](https://openlibrary.org/dev/docs/api/covers) confirma: por padrão, capa ausente devolve imagem vazia; `default=false` devolve 404 e permite fallback por onError no cliente.
- Preservados UUID/ID da obra, autor, título português selecionado e formato JSON. Não trocar capa pela de outra edição arbitrária: o critério atual conserva a primeira edição portuguesa válida para título; na ausência de sua capa positiva, usa a obra, ou null.

## Arquivos principais alterados

Unidade isolada de bugfix backend (quatro arquivos, incluindo este relatório):

- `api/app/providers/open_library.py`
- `api/tests/test_book_covers.py`
- `api/tests/test_books.py` — apenas duas expectativas de URL e sua formatação
- `docs/backend-covers-session-2026-10-02.md`

Nenhum modelo/migration, serviço de favoritos/re-roll, configuração/chave/provider/modelo LLM, TTL ou dado legado/snapshot foi alterado pelo Backend. README/Spec/índice ADR pendentes não foram editados nesta retomada. Maestro possui stage/commits e os três documentos compartilhados.

## Decisões técnicas

- Bug comprovado por reprodução pura: obra `cover_i=123` + primeira edição PT `cover_i=-1` ou `0` gerava `cover_url=None`, perdendo a capa válida da obra. Banco reproduziu independentemente. O payload real afetado ainda não foi confirmado por HTTP nesta sessão.
- Não fazer requisição por capa durante normalização nem adicionar enriquecimento em lote. A URL de capa permanece derivada de metadados reais; status/tamanho no navegador decide fallback.
- Não reescrever catálogo/snapshots antigos nem invalidar TTL/cache incidentalmente. `get_by_id` pode devolver catálogo persistido antigo; favoritos conservam primeiro snapshot. Frontend precisa tratar URLs antigas sem default=false e imagem branca 1×1 via naturalWidth/naturalHeight, além de onError. Asset de livro local deve exigir provider=local para não casar homônimos externos por título.
- Nenhum restart da API efetuado nesta tarefa. Provider corrigido é código em disco; o processo preexistente não tem reload automático e continua executando a versão carregada antes do patch. Aplicação do patch em runtime exige janela coordenada pelo Maestro e verificação de identidade do listener antes de reiniciar.

## Estado atual e evidências

### Diagnóstico read-only

- API conhecida: **PID 37452**, **sessão exec 27472**, `127.0.0.1:8000`; banco `api/.local/gandalf.db` via local.py. GET `/api/v1/system/status` 200, catalog=online/Groq configurado/modelo original; GET `/health/ready` 200, SQLite/schema ok. Sem uso de LLM para diagnosticar capas.
- GET `/api/v1/books/search?q=O+Hobbit&limit=3` 200 retornou um item real do catálogo local, UUID `009af6d0-f978-5886-98f0-b56625753148`, autores J. R. R. Tolkien e `cover_url=null`. É fallback híbrido; não prova funcionamento da fonte externa. Para provider=local, capa de apoio da interface é possível; para externo/null, placeholder seguro.
- Leitura SQLite própria com URI `mode=ro` e `PRAGMA query_only=ON`: exemplos públicos já catalogados `OL17365W` (“2001”) → `https://covers.openlibrary.org/b/id/11344400-M.jpg`; `OL17391W` (“2010, odyssey two”) → `https://covers.openlibrary.org/b/id/4973783-M.jpg`. Sem consulta a dados privados de contas nem escrita no catálogo.
- Auditoria independente Banco em `docs/database-covers-session-2026-10-02.md`: 206 livros Open Library (32 sem capa) e quatro locais (quatro sem capa), 174 URLs M sem default=false; nenhum UUID Open Library divergente. Cinco caches BOOK todos expirados, 15 itens/dois null, sem divergência do catálogo; zero cache BOOK ativo, zero origens e zero favoritos BOOK nesse snapshot. Ausência de capa pode ser metadado legítimo; não afirmar que todos os 32 casos são causados pelo bug corrigido.
- Duas consultas públicas limitadas, `The Hobbit` e `Looking for Alaska`/John Green, fields atuais/edições, limit=3, lang=pt: ConnectError no cliente comum. Mesmas consultas em require_escalated também falharam. Diagnóstico de ambiente mostrou proxies HTTP/HTTPS/ALL herdados apontando `http://127.0.0.1:9` (sem credenciais), explicando o caminho com proxy. Rodada elevada explícita `trust_env=False`, TLS validado, também falhou ConnectError; portanto remover esse proxy apenas no cliente de diagnóstico não restabeleceu transporte. Ambiente global e aplicação não alterados.
- Nenhuma resposta JSON externa real nem imagem foi recebida: HTTPS/formato/tamanho M conferidos no código e nos dados públicos catalogados, **status HTTP/dimensões reais de capa não comprovados**. Nenhuma chamada Groq, alteração de chave/cota ou retry LLM nesta retomada. Não aumentar probes diante da falha de transporte já estabelecida.
- Probes são scripts ignorados em `.impeccable/runtime/backend-cover-probe.py` e `backend-cover-probe-direct.py`; evidência sanitizada em `backend-covers-probe-20261002.json`. Só URLs/títulos/IDs públicos, status e tipos de exceção; nenhum `.env`, segredo ou corpo upstream.

### Testes e revisão

Comandos executados de `api/`:

```powershell
.\.venv\Scripts\python.exe -m ruff format app/providers/open_library.py tests/test_book_covers.py tests/test_books.py
.\.venv\Scripts\python.exe -m ruff check app/providers/open_library.py tests/test_book_covers.py tests/test_books.py
.\.venv\Scripts\python.exe -m ruff format --check app/providers/open_library.py tests/test_book_covers.py tests/test_books.py
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_book_covers.py --tb=short
```

- **22 passed**, 0,30 s; fakes/normalização pura, sem rede/banco/processos. Casos cobrem edição inválida (None/0/-1/bool/string/float), capa positiva preferida, fallback para obra, ausência de capa/JSON null, forma JSON inalterada, UUID/autor/título e edição sem campo de capa.
- Ruff **PASS** / **3 files already formatted**. `git diff --check` seletivo **PASS**; diff revisado para somente normalizador/duas expectativas de URL.
- Maestro informou **366 passed / 1 warning**, 74,80 s, da suíte API anterior ao bugfix em ambiente normal fora do sandbox, inclusive três testes multiprocessos antes bloqueados. Não duplicada pelo Backend. Após congelar estes três arquivos, Maestro executará o subset novo `test_book_covers.py` + `test_books.py`; o resultado posterior deve ser registrado na consolidação dele.
- HEAD observado durante a revisão: `318d97a feat: persiste favoritos individuais por conta`. Commits favoritos/re-roll e este bugfix são serializados pelo Maestro; Backend não fez stage/commit/push.

### Checkpoint final e plano de runtime

- Maestro confirmou favoritos em `318d97a`, re-roll em `f2adc7c` e subset pós-bugfix `tests/test_books.py` + `tests/test_book_covers.py`: **38 passed**, executados normalmente fora do sandbox. HEAD `f2adc7c` conferido pelo Backend. Este relatório e os três arquivos de código/testes estão liberados para commit seletivo de capas pelo Maestro.
- Identidade atual confirmada por leitura escalada de Get-NetTCPConnection/Get-CimInstance: listener `127.0.0.1:8000` pertence ao **PID 37452**; executável `C:\Users\vinic\AppData\Local\Programs\Python\Python312\python.exe`, comando `"C:\Users\vinic\AppData\Local\Programs\Python\Python312\python.exe" local.py`. Origem é a sessão exec 27472 iniciada de `api/`; banco conhecido `api/.local/gandalf.db`. O launcher da venv pode aparecer como executável Python base no processo Windows.
- Na leitura **escalada atual**, HTTP_PROXY/HTTPS_PROXY/ALL_PROXY estão **ausentes**. No ambiente comum anterior havia loopback9. Não afirmar que toda elevação herda o proxy bloqueado: verificar o ambiente efetivo do novo launcher. Probes públicos elevados anteriores, inclusive trust_env=False, falharam ConnectError; ausência de proxy agora não comprova rede externa. Nenhuma nova rodada externa realizada após instrução de parar.
- Plano seguro, **não executado**: depois do commit, revalidar listener/PID/comando; autorizar janela de restart somente dessa API. Encerrar graciosamente a sessão original se acessível, ou parar somente o PID verificado, sem comandos por nome/árvore. Esperar liberação de 8000 antes de iniciar uma única substituta.
- Iniciar de `api/` com `.venv/Scripts/python.exe local.py`, `GANDALF_ONLINE=1`, preservando dados `.local`/configuração existente. Preferir launcher normal fora do sandbox ou escalado verificado; subprocess.Popen com cwd explícito, ambiente próprio e CREATE_NO_WINDOW evita o conflito Path/PATH observado no Start-Process anterior. Não modificar proxy global: se algum proxy loopback9 de bloqueio for herdado, remover **somente esse valor exato** do ambiente do filho; preservar quaisquer proxies reais e demais configurações.
- Após iniciar, validar apenas status/readiness locais e a normalização pura da URL do provider, sem nova chamada LLM/consulta externa. A URL nova pode coexistir com URLs legadas em cache/catalog/favoritos: não invalidar TTL, não reescrever dados/snapshots e não anunciar atualização retroativa. Mantidas chave, provider, modelo e cota. Até a janela autorizada, PID 37452 continua intacto com código antigo carregado.

## Próximos passos

- Maestro validar subset novo, registrar resultado e commitar somente a unidade de quatro arquivos acima; preservar commits/hunks de favoritos e re-roll separados.
- Frontend concluir fallback por erro/1×1, restaurar estado da imagem quando URL mudar, limitar assets locais ao provider correto e verificar exibição de capa na busca/livro selecionado de ReadWithMusic. Sua entrega/validação visual e de navegador são separadas.
- Após commit e com janela de runtime autorizada, Maestro confirmar listener pertence à instância identificada e carregar provider corrigido sem encerrar processos alheios. Não afirmar que API 8000 já usa o patch.
- Quando transporte público do ambiente funcionar, verificar amostra limitada de uma edição portuguesa e sua cover_url/status/dimensões reais, sem LLM nem crawls. Não reescrever catálogo/favoritos antigos para atualizar capas; fallback UI trata legado.
