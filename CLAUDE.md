# Node Data — Prefeitura — Instruções para o Claude Code

## Sobre o Projeto

Node Data Prefeitura é uma plataforma SaaS que coleta feedback de cidadãos via WhatsApp, com análise de sentimento por IA e dashboards em tempo real para gestores municipais.

Stack: Flask (Python), Supabase, Evolution API, OpenAI, Coolify/Docker.

O sistema lida com dados sensíveis de cidadãos (LGPD) e roda em produção para prefeituras.

**Porta:** 5002

## Estrutura do Repositório

```
server.py          — App Flask principal
Dockerfile         — Container (Gunicorn, porta 5002)
requirements.txt   — Dependências Python
.env.example       — Template de variáveis de ambiente
templates/         — Dashboard HTML (data_node.html)
static/            — Logo, ícones, manifest PWA
execution/         — Scripts SQL e Python determinísticos
directives/        — SOPs em Markdown
AGENTE.md          — Arquitetura de 3 camadas
PRODUCTION_CHECKLIST.md — Regras de qualidade e segurança
```

## Arquitetura de Trabalho

Siga a arquitetura de 3 camadas descrita no `AGENTE.md`:
1. **Directive** (o que fazer) → arquivos em `directives/`
2. **Orchestration** (decisões) → você, o agente
3. **Execution** (fazer o trabalho) → scripts em `execution/`

Antes de escrever um script novo, sempre verifique se já existe algo em `execution/` que resolve. Só crie scripts novos se necessário.

## Regras de Produção

Sempre siga as regras de qualidade e segurança descritas em `PRODUCTION_CHECKLIST.md` ao:
- Analisar código existente
- Sugerir mudanças
- Criar código novo
- Revisar antes de deploy

## Regras que Valem Sempre

### Segurança
- Nunca coloque chaves, tokens ou senhas no código — sempre em `.env`
- Sempre valide a origem dos webhooks recebidos
- Dados de cidadãos são protegidos por LGPD — nunca exponha em logs

### Código
- Sempre use try/except em chamadas externas (Supabase, Evolution API, OpenAI)
- Sempre configure timeout nas requisições HTTP (mínimo 10s)
- Sempre valide inputs antes de processar
- Sempre adicione logs nos pontos críticos
- Sempre mascare dados pessoais nos logs (telefone, CPF)
- Retorne 200 rápido nos webhooks e processe pesado em background

### Estilo
- Python com type hints quando possível
- Docstrings em português
- Nomes de variáveis descritivos em português ou inglês
- Comentários explicando o "porquê", não o "o quê"
