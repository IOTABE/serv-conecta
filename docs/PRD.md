# PRD — ServConecta

| Campo | Valor |
| --- | --- |
| Produto | ServConecta |
| Tipo | Marketplace de serviços locais (web) |
| Versão do documento | 1.0 |
| Data | 2026-08-21 |
| Status | Em desenvolvimento (MVP funcional) |

---

## 1. Visão Geral

### 1.1 Problema

Encontrar profissionais de serviços (encanadores, eletricistas, diaristas, professores particulares etc.) é fragmentado: grupos de WhatsApp, indicações boca a boca e classificados sem verificação. Do outro lado, profissionais autônomos têm pouca visibilidade digital e nenhum canal estruturado para receber demandas, negociar e conversar com clientes.

### 1.2 Solução

O **ServConecta** é uma plataforma web que conecta **profissionais (prestadores)** e **clientes**, permitindo que cada lado publique o que oferece ou o que precisa:

- **Ofertas**: o profissional publica seu serviço com preço, unidade (hora/diária/serviço), cidade e imagem.
- **Solicitações**: o cliente publica o que precisa, com orçamento estimado, prazo e cidade.
- **Propostas**: profissionais respondem às solicitações com valor e descrição.
- **Chat**: negociação direta entre cliente e profissional, vinculada à solicitação/oferta.
- **Contratação**: fluxo de contratar diretamente uma oferta publicada.

Ambos os lados se encontram no mesmo lugar: quem oferta encontra demanda; quem demanda encontra oferta.

### 1.3 Diferenciais

- Duas frentes de descoberta simétricas (ofertas × solicitações).
- Chat integrado por solicitação, sem expor contato antes da negociação.
- Selo de prestador verificado.
- Painel administrativo para curadoria e moderação.

---

## 2. Objetivos e Métricas de Sucesso

| Objetivo | Métrica | Meta MVP |
| --- | --- | --- |
| Validar o match oferta ↔ demanda | % de solicitações que recebem ≥ 1 proposta | ≥ 50% |
| Engajamento bilateral | Cadastros completos por semana | 20+ |
| Conversação efetiva | Chats iniciados por solicitação aberta | ≥ 0,5 |
| Conversão em contratação | Contratações iniciadas via página de oferta | acompanhar |
| Qualidade do catálogo | Ofertas com imagem e categoria preenchida | ≥ 80% |

---

## 3. Personas

| Persona | Perfil | Necessidade principal |
| --- | --- | --- |
| **Cliente** (Ana) | Pessoa física buscando um serviço | Encontrar profissional confiável perto, comparar preço e negociar rápido |
| **Profissional** (Carlos) | Autônomo que quer demanda | Divulgar serviço, receber pedidos qualificados e fechar pelo chat |
| **Administrador** | Equipe da plataforma | Curadoria de categorias, moderação de conteúdo, gestão de usuários |

---

## 4. Escopo

### 4.1 Dentro do escopo (MVP)

Autenticação com auto-login no cadastro, CRUD de ofertas (com upload de imagem), CRUD de solicitações com ciclo de status, propostas em solicitações, chat por solicitação com atualização incremental, fluxo de contratação de oferta, listagens com busca/filtro/paginação e administração via Django Admin.

### 4.2 Fora do escopo (por enquanto)

Pagamentos online, avaliação/reputação pós-serviço, aplicativo mobile nativo, notificações push/e-mail, geolocalização por raio, verificação automática de identidade, API pública.

---

## 5. Requisitos Funcionais

### 5.1 Autenticação e Conta

| # | Requisito |
| --- | --- |
| RF-01 | Cadastro de usuário com nome, e-mail e senha; após cadastro bem-sucedido, o usuário é autenticado automaticamente. |
| RF-02 | Login/logout com redirecionamento configurado (`next` respeitado; logout volta à home). |
| RF-03 | Ações de criação (oferta, solicitação, proposta, contratar, chat) exigem usuário autenticado. |

### 5.2 Categorias

| # | Requisito |
| --- | --- |
| RF-04 | Categorias possuem nome único e slug; gerenciadas exclusivamente pelo admin. |
| RF-05 | Ofertas e solicitações podem ser filtradas por categoria nas listagens. |

### 5.3 Ofertas (lado do profissional)

| # | Requisito |
| --- | --- |
| RF-06 | Profissional autenticado cria oferta com título, descrição, categoria, preço, unidade (ex.: SERVIÇO, HORA, DIÁRIA), cidade e imagem opcional (upload). |
| RF-07 | Listagem `/ofertas/` com busca textual, filtros (cidade, categoria) e paginação; ordenada por data de criação decrescente. |
| RF-08 | Página de detalhe exibe dados da oferta, do prestador (com indicador de verificação) e ações: contratar e abrir chat. |
| RF-09 | Destaques na home: ofertas recentes e em evidência. |

### 5.4 Solicitações (lado do cliente)

| # | Requisito |
| --- | --- |
| RF-10 | Cliente autenticado cria solicitação com título, descrição, categoria, cidade, orçamento opcional e prazo opcional. |
| RF-11 | Ciclo de status: `Aberta → Em andamento → Concluída | Cancelada`. |
| RF-12 | Listagem `/solicitacoes/` com busca textual, filtros (categoria, cidade, status) e paginação. |
| RF-13 | Detalhe permite a profissionais enviar proposta e iniciar chat com o cliente. |

### 5.5 Propostas

| # | Requisito |
| --- | --- |
| RF-14 | Profissional envia proposta (valor + descrição) a uma solicitação; **uma proposta por profissional por solicitação** (unicidade). |
| RF-15 | Cliente visualiza as propostas recebidas na sua solicitação e responde via chat. |

### 5.6 Chat

| # | Requisito |
| --- | --- |
| RF-16 | Conversa 1:1 vinculada a uma solicitação (e acessível também a partir da oferta contratável). |
| RF-17 | Participantes enxergam apenas conversas em que são remetente ou destinatário. |
| RF-18 | Novas mensagens são carregadas incrementalmente (polling no endpoint `novas/`) sem recarregar a página. |

### 5.7 Contratação

| # | Requisito |
| --- | --- |
| RF-19 | A partir de uma oferta, o cliente registra interesse em contratar (formulário dedicado), criando o vínculo cliente–prestador e habilitando o chat. |

### 5.8 Administração

| # | Requisito |
| --- | --- |
| RF-20 | Django Admin gerencia usuários, categorias, ofertas, solicitações, propostas e mensagens. |
| RF-21 | Staff pode editar/excluir ofertas e solicitações pela interface do site, com página de confirmação de exclusão e botões visíveis apenas para staff (ver plano `docs/plans/2026-08-21-admin-edit-delete.md`). |
| RF-22 | Seed command popula o banco com dados de demonstração para desenvolvimento. |

---

## 6. Modelo de Dados (resumo)

```
Categoria    (nome, slug)
   │
Oferta       (prestador FK User, categoria FK, titulo, descricao, preco,
              unidade, cidade, imagem, prestador_verificado, timestamps)
Solicitacao  (cliente FK User, categoria FK, titulo, descricao, orcamento?,
              cidade, prazo?, status[aberta|em_andamento|concluida|cancelada],
              timestamps)
Proposta     (solicitacao FK, profissional FK User, valor, descricao;
              unique(solicitacao, profissional))
MensagemChat (solicitacao FK, remetente FK User, destinatario FK User,
              mensagem, criado_em)
```

Regras: exclusão de usuário cascata em suas ofertas/solicitações/mensagens; exclusão de categoria mantém registros (`SET_NULL`).

---

## 7. Requisitos Não-Funcionais

| Categoria | Requisito |
| --- | --- |
| Stack | Django 5.x (templates server-side), Pillow para imagens; **SQLite em desenvolvimento, PostgreSQL em produção** (`DJANGO_ENV=producao`); estáticos servidos por **WhiteNoise** em produção; HTTPS/HSTS obrigatórios em produção. |
| UI | Material Design com glassmorphism (`.glass`, backdrop-filter); fontes Roboto + Material Symbols; responsivo (mobile-first). |
| Segurança | Proteção CSRF em todos os formulários; senhas com hash do Django; autorização por login/staff; uploads validados como imagem. |
| Performance | Listagens paginadas; consultas com `select_related` onde aplicável; imagens otimizadas no upload (futuro). |
| i18n | Interface em pt-BR (`LANGUAGE_CODE = pt-br`, fuso America/Sao_Paulo). |
| Manutenibilidade | Rotas nomeadas em todos os templates; apps separados (`config` / `servconecta`); migrações versionadas. |

---

## 8. Fluxos Principais

1. **Publicar oferta**: entrar → "Nova oferta" → preencher formulário (+imagem) → publicar → aparece nas listagens/home.
2. **Contratar serviço**: buscar/filtrar ofertas → detalhe → "Contratar" → formulário → vínculo criado → chat liberado.
3. **Pedir um serviço**: entrar → "Nova solicitação" → publicar → profissionais enviam propostas → cliente negocia por chat → status evolui até conclusão/cancelamento.
4. **Negociar**: detalhe da solicitação → chat com o interessado → mensagens novas chegam por polling.

---

## 9. Roadmap

| Fase | Conteúdo | Status |
| --- | --- | --- |
| F1 — MVP | Auth, ofertas, solicitações, propostas, chat, contratar, admin, seed | ✅ Implementado |
| F2 — Curadoria | Editar/excluir como staff na interface, mensagens de feedback | 🔜 Plano pronto (`docs/plans/2026-08-21-admin-edit-delete.md`) |
| F3 — Confiança | Avaliações pós-serviço, reputação, verificação de prestadores | Backlog |
| F4 — Retenção | Notificações por e-mail, painel "minhas atividades", favoritos | Backlog |
| F5 — Monetização | Planos de destaque para ofertas, comissão por intermediação | Backlog |
| F6 — Produção | PostgreSQL, storage de mídia, deploy, monitoramento | Backlog |

---

## 10. Riscos e Mitigações

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Liquidez inicial (sem ofertas nem demandas) | Alto | Seed de dados demo; foco em uma cidade/categoria nicho primeiro |
| Abuso/spam no chat e anúncios | Médio | Moderação via admin (RF-21), denúncias (futuro) |
| Chat por polling escala mal | Médio | Migração futura para WebSockets/Channels |
| Uploads de imagem maliciosos | Médio | Validação Pillow, limites de tamanho, storage isolado em produção |
| Pagamentos fora da plataforma | Baixo (MVP) | Aceito no MVP; monitorar para fase de monetização |

---

## 11. Critérios de Aceite do MVP

- [ ] Usuário consegue se cadastrar, entrar e sair.
- [ ] Profissional cria oferta com imagem e ela aparece na listagem e na home.
- [ ] Cliente cria solicitação e recebe propostas de profissionais.
- [ ] Chat funciona entre cliente e profissional dentro de uma solicitação, atualizando sem reload.
- [ ] Fluxo de contratação de oferta conclui sem erros e libera conversa.
- [ ] Busca, filtro e paginação operam nas duas listagens.
- [ ] Admin gerencia todas as entidades; staff tem ações de edição/exclusão no site.
