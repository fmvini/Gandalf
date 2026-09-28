# ADR-0006 — JWT curto e refresh rotativo

**Estado:** Aceita para a implementação inicial da API.

## Contexto

O frontend SPA precisa autenticar chamadas à API e manter sessões sem exigir login frequente. O sistema também deve limitar o impacto de token roubado e permitir revogação de sessões.

## Decisão

Usar access token JWT HS256 de 15 minutos, com claims mínimos e algoritmo fixado na validação. `JWT_SECRET` deve ter pelo menos 32 bytes e vir do ambiente. Usar refresh token opaco de 7 dias, rotativo a cada uso, armazenado apenas como hash no banco e associado a uma família de sessão. Reuso de token já consumido revoga a família. Login e refresh entregam ambos os tokens no corpo JSON; o cliente deve mantê-los apenas em memória. Ao recarregar a página, a sessão termina e o usuário faz login novamente. Reavaliar cookie `HttpOnly; Secure; SameSite` quando a topologia de domínios e a proteção CSRF estiverem definidas.

## Alternativas consideradas

- **Sessão inteiramente no servidor:** revogação simples, mas depende de armazenamento e afinidade operacional próprios.
- **Access token longo sem refresh:** menos endpoints, porém amplia a janela de abuso.
- **Refresh em `localStorage`:** fácil de implementar, porém expõe o token a XSS.
- **Refresh no corpo e em memória:** opção adotada inicialmente; a sessão se perde ao recarregar a página.

## Consequências e validação

A rotação usa transação e bloqueio da linha do refresh token em PostgreSQL. Os testes atuais cobrem expiração, assinatura/algoritmo, logout, reuso e ownership em SQLite; o fluxo completo ainda requer validação em PostgreSQL. A opção de cookie permanece futura e exigirá testes de CSRF e de domínios antes de ser adotada.

**Referências:** [Escopo §25](../00-Escopo-Detalhado.md#25-autenticação), [Security Specification §5](../09-security-specification.md#5-autenticação-seção-25-do-escopo), [API Specification](../05-API-Specification.md).
