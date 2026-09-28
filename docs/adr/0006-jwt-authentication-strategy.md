# ADR-0006 — JWT curto e refresh rotativo

**Estado:** Proposta; mecanismo de entrega do refresh token e assinatura ainda precisam de decisão final.

## Contexto

O frontend SPA precisa autenticar chamadas à API e manter sessões sem exigir login frequente. O sistema também deve limitar o impacto de token roubado e permitir revogação de sessões.

## Decisão proposta

Usar access token JWT de vida curta (referência inicial: 15 minutos) com claims mínimos e algoritmo fixado na validação. Usar refresh token de vida mais longa, rotativo a cada uso, armazenado apenas como hash no banco e associado a uma família de sessão. Reuso de token já consumido revoga a família. O cliente mantém o access token em memória. A opção preferida para refresh é cookie `HttpOnly; Secure; SameSite` restrito ao endpoint de refresh, sujeita à topologia de domínios e proteção CSRF; o contrato final de entrega permanece em aberto.

## Alternativas consideradas

- **Sessão inteiramente no servidor:** revogação simples, mas depende de armazenamento e afinidade operacional próprios.
- **Access token longo sem refresh:** menos endpoints, porém amplia a janela de abuso.
- **Refresh em `localStorage`:** fácil de implementar, porém expõe o token a XSS.
- **Refresh no corpo e em memória:** evita cookie/CSRF, mas a sessão se perde ao recarregar a página.

## Consequências e validação

A rotação exige transação segura e tratamento de concorrência. Antes de implementar, fixar algoritmo de assinatura e transporte do refresh, alinhar [API](../05-API-Specification.md) e [Security Specification](../09-security-specification.md), e testar expiração, logout, reuso, CSRF, cookies entre domínios e ownership. Nenhuma dessas variantes deve ser tratada como validada apenas por este registro.

**Referências:** [Escopo §25](../00-Escopo-Detalhado.md#25-autenticação), [Security Specification §5](../09-security-specification.md#5-autenticação-seção-25-do-escopo), [API Specification](../05-API-Specification.md).
