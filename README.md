# FABRITAG

Monorepo/workspace do projeto FABRITAG com:
- Frontend em SvelteKit (`src/routes`, `src/components`, `src/lib/components`)
- Backend Flask + PostgreSQL (`src/lib/server`)
- Firmware para leitura RFID (ESP32 + PN5180) (`sketch_feb28a`)
- Documentação e artefatos auxiliares (`docs`, `fabritag_db.json`)

## Como rodar (resumo)

```sh
pnpm install
pnpm dev
```

Para o backend Python (API Flask), use os arquivos em `src/lib/server` e configure variáveis de ambiente para o banco PostgreSQL.

## Estrutura de pastas

```text
fabritag/
├─ docs/                                   # Documentação do projeto (PDFs e materiais de apoio)
│  └─ fabritag_IC.pdf
├─ firmware/                          # Firmware do leitor RFID em ESP32/PN5180
│  └─ firmware.ino
├─ src/                                    # Código-fonte principal do frontend e integração
│  ├─ components/                          # Componentes de interface de uso geral
│  ├─ lib/                                 # Biblioteca compartilhada (assets, UI e backend Python)
│  │  ├─ assets/                           # Ícones e imagens usados no app
│  │  ├─ components/                       # Componentes reutilizáveis (Card, Container)
│  │  └─ server/                           # Backend Flask, schema SQL e dependências Python
│  ├─ routes/                              # Rotas/páginas do SvelteKit
│  │  ├─ dashboard/                        # Página de visão geral e métricas
│  │  ├─ infraestrutura/                   # Páginas de infraestrutura (armazéns, blocos, sensores)
│  │  └─ movimentacao/                     # Página e lógica de movimentações
│  ├─ app.css
│  └─ app.html
├─ static/                                 # Arquivos estáticos servidos diretamente
│  └─ robots.txt
├─ fabritag_db.json                        # Base/fixture local em JSON para testes/dados
├─ jsconfig.json
├─ package.json
├─ pnpm-lock.yaml
├─ pnpm-workspace.yaml
├─ svelte.config.js
└─ vite.config.js
```

## Observações

- Pastas de ambiente/ferramenta como `.git`, `.venv`, `.svelte-kit` e `node_modules` não fazem parte da estrutura funcional do código-fonte.
- O frontend usa rotas do SvelteKit em `src/routes` e integra com a API do backend.
