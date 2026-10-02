# ADR-0006 — JWT curto e refresh rotativo

**Estado:** Aceita para a implementação inicial da API.

## Contexto

O frontend SPA precisa autenticar chamadas à API e manter sessões sem exigir login frequente. O sistema também deve limitar o impacto de token roubado e permitir revogação de sessões.

## Decisão

Usar access token JWT HS256 de 15 minutos, com claims mínimos e algoritmo fixado na validação. `JWT_SECRET` deve ter pelo menos 32 bytes e vir do ambiente. Usar refresh token opaco de 7 dias, rotativo a cada uso, armazenado apenas como hash no banco e associado a uma família de sessão. Reuso de token já consumido revoga a família. Login e refresh entregam ambos os tokens no corpo JSON; o cliente deve mantê-los apenas em memória. Ao recarregar a página, a sessão termina e o usuário faz login novamente. Reavaliar cookie `HttpOnly; Secure; SameSite` quando a topologia de domínios e a proteção CSRF estiverem definidas.

Em PostgreSQL/READ COMMITTED, todas as operações de refresh/replay serializam a família com `pg_advisory_xact_lock` antes de bloquear a linha do token. A chave inteira de 64 bits deriva de SHA-256 de um namespace fixo e do UUID da família. O lookup inicial identifica apenas a família, sem row lock; após aguardar o advisory lock, uma nova consulta com `FOR UPDATE` e `populate_existing` relê o estado. O lock termina com commit/rollback. SQLite preserva o consumo por UPDATE condicional atômico.

## Alternativas consideradas

- **Sessão inteiramente no servidor:** revogação simples, mas depende de armazenamento e afinidade operacional próprios.
- **Access token longo sem refresh:** menos endpoints, porém amplia a janela de abuso.
- **Refresh em `localStorage`:** fácil de implementar, porém expõe o token a XSS.
- **Refresh no corpo e em memória:** opção adotada inicialmente; a sessão se perde ao recarregar a página.

## Consequências e validação

Bloquear somente a linha do token foi insuficiente: em 2026-10-02, a corrida real entre replay de ancestral e rotação de descendente deixou um novo refresh ativo fora do snapshot do UPDATE de revogação. O gate PostgreSQL18.6/READ COMMITTED reproduziu a falha com bloqueio observado; após serializar a família e reler, a mesma corrida retornou rotação200/replay401 e zero tokens ativos. O mesmo-token concorrente também retornou200/401 com zero ativos. Constraints/digests, ownership/logout/expiração/cascade passaram em instância descartável; nenhum schema alterado.

Os 52 testes auth/security cobrem contratos JWT, persistência/rollback, SQLite e protocolo de lock com simulação; o gate real é evidência separada desses probes. Não cobre HTTP entre duas aplicações, logout/refresh concorrentes controlados ou rollout pré-populado. Colisões da chave de 64 bits podem serializar famílias independentes, sem misturar seus dados; família/owner continuam UUIDs nas consultas. A opção de cookie permanece futura e exigirá testes de CSRF e de domínios antes de ser adotada. Resultados e limites: [relatório Backend](../backend-auth-session-2026-10-02.md) e [relatório Banco](../database-auth-session-2026-10-02.md).

**Referências:** [Escopo §25](../00-Escopo-Detalhado.md#25-autenticação), [Security Specification §5](../09-security-specification.md#5-autenticação-seção-25-do-escopo), [API Specification](../05-API-Specification.md).
