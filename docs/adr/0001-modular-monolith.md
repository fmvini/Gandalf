# ADR-0001 — Monólito modular para o backend

**Estado:** Aceita no desenho; ainda não implementada.

## Contexto

O MVP combina autenticação, catálogo, IA, recomendação e integrações externas. A equipe inicial é pequena e o [roadmap](../12-development-roadmap.md) prioriza qualidade de recomendação e entrega incremental. Separar tudo em serviços independentes exigiria deploys, observabilidade e contratos distribuídos antes de haver escala que justifique esse custo.

## Decisão

Construir um único backend FastAPI com módulos e dependências explícitos: `api` → `services` → domínio (`recommendation`) e portas de infraestrutura (`ai`, `providers`, `repositories`). O pacote de recomendação não importa FastAPI, implementações de provider nem SQLAlchemy. O frontend React acessa uma API REST versionada.

## Alternativas consideradas

- **Microservices desde o início:** escalam componentes separadamente, mas acrescentam coordenação, latência e operações.
- **Monólito sem fronteiras:** inicia rápido, mas mistura ranking, HTTP e persistência e dificulta testes e troca de fornecedores.

## Consequências e validação

Um deploy de backend simplifica o MVP e permite testes isolados. O processo único limita escala independente e exige vigilância contra acoplamento entre pacotes. Verificar fronteiras por revisão e testes de importação quando o código existir; reavaliar a divisão somente diante de necessidades medidas.

**Referências:** [Escopo §§32–35](../00-Escopo-Detalhado.md#32-arquitetura), [Arquitetura §4](../03-System-Architecture.md#4-arquitetura-em-camadas).
