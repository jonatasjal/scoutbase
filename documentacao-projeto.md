# ScoutBase — Plataforma de Conexão entre Atletas de Base e Olheiros/Patrocinadores

**Documentação de Projeto — Versão 1.1**
**Data:** Setembro – Outubro de 2026

---

## 1. Sumário Executivo

O ScoutBase é uma plataforma digital que conecta atletas de base — começando pelo futebol, com expansão planejada para outros esportes — a olheiros, clubes e patrocinadores. O objetivo é reduzir a distância entre talento e oportunidade, especialmente para atletas fora dos grandes centros urbanos, permitindo que construam um "currículo esportivo digital" com vídeos, estatísticas e histórico, e sejam encontrados por meio de busca avançada.

Este documento cobre a visão de negócio, o público-alvo, o modelo de monetização, os requisitos funcionais e não funcionais, as considerações legais, a arquitetura do sistema, o modelo de dados e o roadmap de desenvolvimento — servindo como guia de referência para todo o ciclo de construção do projeto, da concepção à publicação local.

---

## 2. Contexto de Mercado

Esse não é um espaço vazio — e isso é bom: significa que existe demanda validada, mas também que é preciso ter clareza sobre diferenciação. Alguns players relevantes hoje:

- **On Scout** — rede de assinatura que conecta atletas, clubes, olheiros e empresários, com perfis detalhados de habilidades e características físicas, e sem cobrança de comissão sobre transações.
- **Footbao** — plataforma com aporte internacional que usa inteligência artificial para analisar vídeos enviados por jovens atletas, reconhecendo lances como passes e finalizações, e já gerou ao menos um caso real de transferência internacional a partir de vídeos enviados por um atleta brasileiro.
- **TransferRoom** — funciona como uma rede social voltada a agentes, scouts e jogadores para troca de dados.
- **E-Scout** — focada em dar visibilidade estatística ao futebol de base brasileiro, com ranking que pondera o contexto de cada competição.
- **FindPlayer** — aplicativo que usa desafios diários, upload de vídeos e sistema de classificação para conectar atletas a treinadores com base em mérito.

**O que isso significa para o seu projeto:**
- Validação de que o problema é real e o mercado brasileiro é visto como "celeiro" de talentos, inclusive por investidores internacionais.
- O diferencial não deve ser "ter perfil com vídeo" (isso já é padrão), e sim algo como: foco declarado no interior/regiões negligenciadas, simplicidade de uso para quem tem pouca familiaridade digital, ou um modelo de dados multi-esporte desde a concepção (mesmo começando só com futebol).
- Como é um projeto de portfólio no início, a concorrência não é um obstáculo — é uma fonte de inspiração de funcionalidades e um argumento de que a ideia tem mercado real, caso você decida buscar rentabilização no futuro.

---

## 3. Proposta de Valor

**Para o atleta:** visibilidade que ele não teria de outra forma, sem depender de conhecer "a pessoa certa".

**Para o olheiro/clube:** redução do custo e tempo de garimpar talentos presencialmente, com busca filtrada e comparável.

**Para o patrocinador:** acesso a atletas emergentes antes que fiquem caros ou conhecidos, com dados de engajamento.

**Diferencial estratégico sugerido:** iniciar com foco declarado em regiões do interior (que é exatamente o ponto cego das grandes plataformas, mesmo as que dizem cobrir "todo o Brasil"), e desenhar o modelo de dados desde o início pensando em multi-esporte, mesmo implementando só futebol na V1 — isso evita retrabalho estrutural depois.

---

## 4. Personas

### 4.1 Atleta
- Idade: 12 a 23 anos (inclui menores de idade — ver seção de considerações legais)
- Objetivo: ser visto por quem pode abrir uma oportunidade (clube, olheiro, patrocinador)
- Dores: falta de acesso a peneiras, distância dos centros de decisão, falta de saber "como se vender"

### 4.2 Responsável Legal (para atletas menores de idade)
- Pai, mãe ou responsável que gerencia o perfil em nome do atleta menor
- Objetivo: proteger o filho e, ao mesmo tempo, dar visibilidade a ele com segurança

### 4.3 Olheiro / Clube
- Profissional de captação de um clube (de várzea a profissional) ou olheiro independente
- Objetivo: encontrar talentos de forma mais eficiente que métodos tradicionais
- Dores: cobertura geográfica limitada, dificuldade de comparar atletas de contextos diferentes

### 4.4 Patrocinador / Marca
- Empresa ou pessoa física que busca associar sua marca a atletas emergentes
- Objetivo: encontrar atletas com potencial de crescimento antes que fiquem caros

---

## 5. Modelo de Negócio e Monetização

| Modelo | Público | Descrição |
|---|---|---|
| Freemium | Atletas | Perfil básico gratuito; plano pago libera mais vídeos, destaque na busca e estatísticas avançadas |
| Assinatura | Olheiros/Clubes | Acesso à busca avançada e contato direto é pago (modelo similar ao LinkedIn Recruiter) |
| Comissão | Todos | Taxa sobre conexões que evoluem para contrato — difícil de rastrear tecnicamente, mas é um argumento de pitch de negócio forte |
| Destaque pago | Atletas/Patrocinadores | Atletas pagam para aparecer em posições de destaque na busca |

**Observação de negócio:** no MVP, não vale a pena implementar cobrança de verdade. O foco é desenhar o sistema para que a lógica de planos (grátis vs. pago) já exista estruturalmente — por exemplo, um campo `plano` no usuário — mesmo que o pagamento em si seja simulado ou nem exista ainda.

---

## 6. Requisitos Funcionais (MVP)

1. Cadastro e login com dois tipos de perfil: Atleta e Olheiro/Clube
2. Edição de perfil do atleta: dados pessoais, posição, categoria, clube atual, histórico, biografia
3. Upload de vídeo (ou link externo, ex: YouTube) associado ao perfil
4. Registro de estatísticas por competição/temporada (gols, assistências, jogos)
5. Busca de atletas com filtros: esporte, posição, faixa etária, região, categoria
6. Visualização de perfil público do atleta
7. Sistema de favoritos (lista de observação do olheiro)
8. Mensagens diretas entre olheiro e atleta (ou responsável, se menor de idade)
9. Dashboard simples para o atleta ver quantas visualizações seu perfil recebeu

### 6.1 Requisitos Funcionais — Fase 2 (pós-MVP)
- Estatísticas avançadas integradas a dados de campeonatos
- Selo de "perfil verificado"
- Avaliações/recomendações de técnicos anteriores
- Notificações e feed de atividades
- Suporte a múltiplos esportes (vôlei, atletismo)
- Painel para responsáveis legais gerenciarem perfis de menores

## 7. Requisitos Não Funcionais

- **Segurança:** senhas com hash (nunca em texto puro), autenticação por token
- **Privacidade:** dados de menores de idade com controle de acesso mais restrito
- **Performance:** busca com filtros deve responder rapidamente mesmo com muitos perfis cadastrados (pensar em índices no banco desde o modelo de dados)
- **Escalabilidade de modelo:** o esquema de dados deve ser desenhado para multi-esporte desde o início, mesmo que a V1 implemente só futebol
- **Manutenibilidade:** código organizado em camadas (separar regras de negócio, acesso a dados e API)
- **Portabilidade:** projeto deve subir localmente com um único comando (Docker Compose), sem depender de serviços externos pagos

---

## 8. Considerações Legais e Éticas (importante — não pular)

Como o projeto envolve **menores de idade**, mesmo sendo um projeto de portfólio, vale a pena tratar isso com seriedade desde o design, porque isso também é um diferencial técnico/profissional a apresentar:

- **LGPD (Lei Geral de Proteção de Dados):** dados de menores de idade exigem consentimento específico de um responsável legal. No modelo de dados, isso significa ter uma entidade `ResponsavelLegal` vinculada ao atleta menor, e regras de que o cadastro/edição de um atleta menor só é validado com um responsável associado.
- **Exposição de imagem de menores:** vídeos e fotos de atletas menores de idade são um ponto sensível. Vale documentar (mesmo que simulado) políticas como: vídeos mostrando só o atleta em contexto esportivo, sem dados de localização exata da residência, com termo de uso claro sobre quem pode ver o quê.
- **Termos de uso e política de privacidade:** mesmo em um projeto de portfólio, escrever uma versão simplificada desses documentos mostra maturidade de produto para quem for avaliar o projeto (recrutador, investidor, etc.)
- **Diferenciação de visibilidade por idade:** perfis de atletas menores de idade poderiam ter, por padrão, menos informação pública visível (ex: sem geolocalização exata) até que um responsável libere contato.

---

## 9. Arquitetura do Sistema (lógica, sem código)

### 9.1 Visão geral em camadas

```
[Cliente Web - Frontend]
        |
        | HTTP/REST (JSON)
        v
[API Backend]
        |
   +----+----+
   |         |
[Regras   [Acesso a
de negócio] dados/ORM]
   |         |
   +----+----+
        v
 [Banco de Dados PostgreSQL]

[Armazenamento de mídia] <-- vídeos/fotos, local em disco (simulando um bucket de nuvem)
```

### 9.2 Por que essa separação em camadas importa

- **Frontend** cuida só de exibir dados e capturar interação do usuário — não deve conter regra de negócio (ex: "quem pode ver o telefone de um atleta menor" é decisão do backend, não do frontend).
- **Camada de regras de negócio** (services) concentra a lógica: validações, permissões, cálculos. Isso facilita testar sem precisar de banco de dados real.
- **Camada de acesso a dados** isola o banco — se um dia você trocar PostgreSQL por outro banco, só essa camada muda.
- **API** expõe endpoints REST (ex: `GET /atletas`, `POST /atletas`, `GET /atletas/{id}`) que o frontend consome.

### 9.3 Autenticação e autorização

- Login gera um token (JWT) que o frontend armazena e envia em cada requisição.
- O backend usa esse token para saber quem é o usuário e qual seu tipo (atleta, olheiro, responsável).
- Regras de autorização ficam centralizadas: por exemplo, só o próprio atleta (ou seu responsável, se menor) pode editar seu perfil; só olheiros com plano pago podem enviar mensagem direta.

### 9.4 Upload e armazenamento de mídia

- No ambiente local, vídeos/fotos ficam salvos em uma pasta do servidor, com o caminho salvo no banco de dados.
- A arquitetura já prevê que essa pasta local pode, no futuro, ser substituída por um serviço de nuvem (ex: S3) sem mudar a lógica do restante do sistema — a camada de "armazenamento" fica isolada por trás de uma interface própria.

---

## 10. Modelo de Dados (Entidades e Relacionamentos)

### 10.1 Entidades principais

- **Usuario**: dados de login e tipo de conta (atleta, olheiro, responsável, patrocinador)
- **Atleta**: dados esportivos vinculados a um Usuario (posição, categoria, esporte, cidade/estado, clube atual, biografia)
- **ResponsavelLegal**: vincula um responsável a um ou mais atletas menores de idade
- **VideoAtleta**: vídeos vinculados a um atleta
- **EstatisticaAtleta**: registros de desempenho por competição/temporada
- **Olheiro**: dados profissionais vinculados a um Usuario (organização, cargo, status de verificação)
- **Favorito**: relação entre um Olheiro e um Atleta (lista de observação)
- **Mensagem**: comunicação entre um Olheiro e um Atleta (ou seu responsável)
- **Avaliacao**: recomendação de um avaliador sobre um atleta (fase 2)

### 10.2 Relacionamentos principais

- Um `Usuario` pode ser um `Atleta`, um `Olheiro`, ou um `ResponsavelLegal` (relação 1 para 1 com a entidade específica)
- Um `Atleta` menor de idade tem um ou mais `ResponsavelLegal` associados
- Um `Atleta` tem muitos `VideoAtleta` e muitas `EstatisticaAtleta`
- Um `Olheiro` pode ter muitos `Atleta` favoritados (relação muitos-para-muitos via `Favorito`)
- `Mensagem` conecta um `Olheiro` e um `Atleta` (ou responsável) em uma conversa

### 10.3 Por que pensar multi-esporte desde já

Mesmo implementando só futebol na V1, vale desenhar `EstatisticaAtleta` de forma flexível — por exemplo, em vez de colunas fixas tipo "gols" e "assistências", usar uma estrutura mais genérica de "métrica + valor" vinculada ao esporte. Isso evita ter que redesenhar o banco inteiro quando vôlei ou atletismo entrarem, já que as métricas de cada esporte são completamente diferentes.

---

## 11. Stack Tecnológica Recomendada

Como você tem mais familiaridade com Python, a stack abaixo aproveita isso sem abrir mão de um projeto moderno:

| Camada | Tecnologia | Por quê |
|---|---|---|
| Backend | **Python + FastAPI** | Moderno, rápido de aprender, ótima documentação automática de API (Swagger), tipagem que ajuda a evitar erros |
| ORM | **SQLAlchemy** (ou SQLModel, que une Pydantic + SQLAlchemy) | Padrão de mercado em Python para acesso a banco de dados |
| Banco de dados | **PostgreSQL** | Relacional, robusto, ótimo para dados estruturados como os desse projeto |
| Frontend | **React** (com Vite) | Moderno, grande comunidade, muitos recursos de aprendizado |
| Autenticação | **JWT** (biblioteca `python-jose` ou similar) | Padrão simples e amplamente usado |
| Containerização | **Docker + Docker Compose** | Permite subir frontend, backend e banco com um único comando, e documenta exatamente o ambiente do projeto |
| Testes | **Pytest** (backend) | Padrão em Python, fácil de aprender |

Essa combinação (FastAPI + React + PostgreSQL + Docker) é uma stack bastante usada no mercado atualmente, o que também ajuda o projeto a servir como peça de portfólio.

---

## 12. Roadmap de Desenvolvimento (passo a passo lógico)

A lógica aqui é: **cada fase entrega algo que funciona e pode ser demonstrado**, mesmo que pequeno. Isso mantém a motivação de avançar todo dia, como você mencionou.

### Fase 0 — Fundamentos e ambiente (poucos dias)
1. Definir e documentar o modelo de dados final (entidades e relacionamentos)
2. Configurar o ambiente local: estrutura de pastas do backend e do frontend
3. Configurar o banco de dados PostgreSQL localmente (via Docker)
4. Criar a primeira migração de banco (criar as tabelas a partir do modelo de dados)

### Fase 1 — Backend básico (autenticação e cadastro)
1. Criar endpoint de cadastro de usuário (com tipo: atleta ou olheiro)
2. Criar endpoint de login que retorna um token
3. Criar middleware/dependência que valida o token nas rotas protegidas
4. Testar tudo via documentação automática do FastAPI (Swagger), sem precisar de frontend ainda

### Fase 2 — Perfil do atleta
1. Endpoint para o atleta completar seu perfil (posição, categoria, cidade, etc.)
2. Endpoint para upload de vídeo (salvando localmente e registrando no banco)
3. Endpoint para registrar estatísticas
4. Endpoint público para visualizar o perfil de um atleta

### Fase 3 — Busca e descoberta
1. Endpoint de busca de atletas com filtros (esporte, posição, idade, região)
2. Lógica de paginação (não retornar todos os resultados de uma vez)
3. Endpoint de favoritar/desfavoritar atleta (para o olheiro)

### Fase 4 — Comunicação
1. Endpoint para enviar mensagem entre olheiro e atleta
2. Endpoint para listar conversas e mensagens
3. Regra de negócio: se o atleta for menor de idade, a mensagem deveria idealmente notificar/envolver o responsável (mesmo que de forma simplificada no MVP)

### Fase 5 — Frontend
1. Telas de cadastro/login
2. Tela de edição de perfil do atleta
3. Tela de busca com filtros (consumindo a API já pronta)
4. Tela de perfil público do atleta
5. Tela de mensagens

*Observação: a Fase 5 pode começar em paralelo com as fases 2 a 4, já que o backend vai expondo endpoints incrementalmente que o frontend pode consumir aos poucos.*

### Fase 6 — Testes e refinamento
1. Testes automatizados das regras de negócio principais (ex: "atleta menor precisa de responsável")
2. Revisão de segurança básica (senhas, tokens, permissões)
3. Ajustes de usabilidade no frontend

### Fase 7 — Publicação local
1. Escrever o `docker-compose.yml` reunindo backend, frontend e banco
2. Documentar no README como subir o projeto do zero
3. Popular o banco com dados de exemplo (seed) para demonstração

### Fase 8 — Expansão (pós-MVP, se o projeto avançar)
1. Adicionar suporte a um segundo esporte (vôlei, por exemplo), validando se o modelo de dados aguenta sem grandes mudanças
2. Implementar avaliações/recomendações
3. Explorar cobrança real (integração com gateway de pagamento) se decidir seguir para monetização de verdade

### Fase 9 — Análise de vídeo com visão computacional (pós-MVP, experimental)
1. **MVP de análise:** processar vídeos do `VideoAtleta` com detecção de jogadores (YOLO) e estimar métricas básicas — velocidade média, distância percorrida, número de toques
2. **Detecção de eventos (avançado):** identificar automaticamente passes, finalizações e desarmes a partir do vídeo
3. **Comparativo (futuro):** cruzar as métricas extraídas com banco de dados de atletas da mesma posição/categoria para gerar um score de scouting
4. **Stack provável:** Python + Ultralytics (YOLO) + OpenCV, processamento offline em lote (não em tempo real)
5. **Observação:** fase experimental de alto custo computacional — só iniciar após as fases 0-7 consolidadas

---

## 13. Estratégia de Testes

- **Testes unitários:** regras de negócio isoladas (ex: cálculo de quem pode ver o quê no perfil)
- **Testes de integração:** endpoints da API completos, usando um banco de dados de teste
- **Testes manuais guiados:** roteiro de "caminho feliz" (cadastro → perfil → busca → mensagem) para validar antes de cada entrega de fase

---

## 14. Estratégia de Publicação Local

- Todo o projeto sobe com `docker compose up`, reunindo três serviços: banco de dados, backend e frontend
- Variáveis sensíveis (senha do banco, chave de token JWT) ficam em um arquivo de ambiente (`.env`), nunca direto no código
- README documenta: requisitos para rodar (Docker instalado), passo a passo de subida, e como popular dados de exemplo

---

## 15. Métricas de Sucesso (mesmo em ambiente local/demonstração)

- Número de perfis de atletas cadastrados (simulados)
- Número de buscas realizadas
- Taxa de resposta a mensagens (simulada)
- Cobertura de testes automatizados do backend

---

## 16. Próximos Passos Imediatos

1. ✅ Fase 0 — fundamentos, Docker/Postgres, 11 tabelas e migration inicial (commit `8988fe9`, 01/10/2026)
2. ✅ Fase 1 — cadastro, login JWT e rota protegida `/auth/me` (commit `e1ddb84`, 06/10/2026)
3. 🔄 Fase 2 — perfil do atleta:
   - [x] 2.1 Schemas do perfil (`PerfilAtletaDados` / `PerfilAtletaSaida`)
   - [x] 2.2 `PUT /perfil/completar` (criar ou atualizar a ficha, idempotente)
   - [x] 2.3 `GET /perfil/{id}` (perfil público, com 404/422)
   - [x] 2.4 Upload de vídeo ✅ (13/10/2026):
     - 2.4A `POST /videos/upload` — multipart, valida extensão (`.mp4/.mov/.webm`), limite 100 MB, nome com uuid, grava em blocos de 1 MB em `backend/media/uploads/`, registra linha em `video_atleta` (dependência `python-multipart` instalada)
     - 2.4B `GET /perfil/{id}/videos` — lista pública dos vídeos do atleta (mais novo primeiro) + `StaticFiles` montado em `/media` (arquivos de `backend/media` servidos com o Content-Type certo)
     - Bônus 2.4 — rota `/` redireciona para `/docs` (`RedirectResponse`, HTTP 307)
   - [x] 2.5 Estatísticas do atleta ✅ (14/10/2026) — `POST /estatisticas` com **upsert** (re-lançar a mesma métrica atualiza o valor) + `GET /perfil/{id}/estatisticas` público com filtros `?competicao=` / `?temporada=`
   - [x] 2.6 Commit da Fase 2 ✅ — `31c3395` (14/10/2026) "Fase 2: perfil do atleta, videos e estatisticas com upsert"

✅ **Fase 2 encerrada.** Próxima: **Fase 3 — Busca e descoberta** (`GET /atletas` com filtros, paginação, favoritos).

4. ✅ Fase 3 — busca e descoberta (FECHADA 19/10/2026):
   - [x] 3.0 Campo `nome` ✅ (16/10/2026) — coluna em `usuario` + migrations `9ed6706244c1` (cria) e `ecf66b6ee6f0` (remove `atleta.nome` duplicado por engano); cadastro valida 201 com nome
   - [x] 3.1 `GET /atletas` ✅ (16/10/2026) — vitrine pública (join Atleta×Usuario, idade calculada); bloqueio Smart App Control do Windows resolvido no meio (DLLs .pyd barradas)
   - [x] 3.2 Filtros + paginação ✅ (16/10/2026) — `?esporte=&posicao=&estado=&categoria=` + `?pagina=&por_pagina=` com envelope `BuscaAtletasSaida`
   - [x] 3.3 Favoritos ✅ (19/10/2026) — PUT /olheiro/completar (upsert) + POST/DELETE /atletas/{id}/favoritar + GET /meus-favoritos; 409 duplicado, 403 sem perfil olheiro
   - Commit: `ae3e7db`

5. ✅ Fase 4 — Mensagem/chat (FECHADA 20/10/2026):
   - [x] 4.1 Enviar + conversa ✅ (20/10/2026) — `POST /mensagens` + `GET /mensagens/conversa/{outro_id}` (cronológico, só as que participei); roteador `routers/mensagens.py`; `remetente_nome` via dicionário (1 query)
   - [x] 4.2 Lido/não-lido ✅ (20/10/2026) — `PUT /mensagens/lidas/{outro_id}` (update em massa) + `GET /mensagens/nao-lidas` (count); só o destinatário marca como lido
   - [x] 4.3 LGPD ✅ (20/10/2026) — olheiro → atleta menor exige responsável legal com vínculo ativo (senão 403); com vínculo grava `consentimento_responsavel_id` (recibo de auditoria)
   - Commits: `bd2cc01` (4.1+4.2) e `22514b3` (4.3)

6. ✅ Fase 5 — Responsável Legal API (FECHADA 21/10/2026):
   - [x] `POST /responsaveis` — criar vínculo responsável × atleta (só tipo responsavel; 404 atleta inexistente; 409 duplicado)
   - [x] `GET /responsaveis/meus-vinculos` — lista os vínculos ativos do logado
   - [x] `DELETE /responsaveis/{id}` — soft delete (`vinculo_ativo = false`, histórico preservado p/ auditoria; só o dono)
   - [x] Fechou a brecha da LGPD: vínculo agora é criado por API (antes era SQL direto)
   - Commit: `2ee4551`

7. ✅ Fase 6 — Avaliação bidirecional (FECHADA 22/10/2026):
   - [x] `POST /avaliacoes` — olheiro avalia atleta E atleta avalia olheiro (direção decidida pelo tipo de quem loga); upsert 1 nota por par; nota 0–10 + comentário opcional
   - [x] `GET /avaliacoes/{tipo}/{id}` — resumo: média, total e comentários
   - [x] `GET /avaliacoes/minhas` — o que o logado já avaliou
   - [x] Tabela polimórfica via migration `7a282b4eb5c0` (`avaliado_tipo` + `avaliado_id`)
   - Commit: `f6f2192`

8. ✅ Fase 7 — Dashboard de rankings (FECHADA 22/10/2026):
   - [x] `GET /dashboard/top-atletas` — ranking por média de avaliação (GROUP BY + AVG + HAVING + ORDER BY DESC + LIMIT); `?limite` (1–50, default 10)
   - [x] `GET /dashboard/ranking-olheiros` — reputação dos olheiros (mesma engenharia)
   - [x] `GET /dashboard/resumo` — totais: usuários, atletas, olheiros, avaliações, média geral, vídeos, mensagens
   - Commit: `3f8ae44`

9. ✅ Fase 8 — Visualização de perfil (FECHADA 27/10/2026):
   - [x] `GET /perfil/{id}` registra a visita (dependência opcional `get_current_user_optional`: sem token = anônimo, com token = identificado; dono não conta view própria; tracking com try/rollback nunca derruba a busca)
   - [x] `GET /perfil/{id}/visualizacoes` — métricas do dono (total, únicos, anônimas, última, últimos 10 visitantes via outerjoin); 401 sem token, 403 não-dono, 404 atleta inexistente
   - [x] Schemas `VisitanteRecente` / `VisualizacoesSaida`; tabela `visualizacao` (pronta desde a Fase 2, sem migration)
   - Commit: `21314c4`

10. 🔄 Fase 9 — Frontend React (EM ANDAMENTO desde 29/10/2026):
    - [x] 9.1 Setup Vite + proxy `/api` → `:8000` + helper `src/api/client.js`
    - [x] 9.2 Vitrine de atletas (filtros reativos, paginação, cartões) — rotas `/` e componentes `CartaoAtleta`/`Vitrine`
    - [x] 9.3 Perfil do atleta (`/perfil/:id` — ficha, estatísticas agrupadas por competição, player de vídeo)
    - [ ] 9.4 Rankings · [ ] 9.5 Login/cadastro no front · [ ] 9.6 Telas autenticadas

**Endpoints que já respondem hoje:** `GET /health`, `GET /`, `POST /auth/cadastro`, `POST /auth/login`, `GET /auth/me`, `PUT /perfil/completar`, `GET /perfil/{id}`, `GET /perfil/{id}/videos`, `GET /perfil/{id}/estatisticas`, `POST /videos/upload`, `POST /estatisticas`, `GET /atletas`, `PUT /olheiro/completar`, `POST`/`DELETE /atletas/{id}/favoritar`, `GET /meus-favoritos`, `POST /mensagens`, `GET /mensagens/conversa/{id}`, `PUT /mensagens/lidas/{id}`, `GET /mensagens/nao-lidas`, `POST /responsaveis`, `GET /responsaveis/meus-vinculos`, `DELETE /responsaveis/{id}`, `POST /avaliacoes`, `GET /avaliacoes/{tipo}/{id}`, `GET /avaliacoes/minhas`, `GET /dashboard/top-atletas`, `GET /dashboard/ranking-olheiros`, `GET /dashboard/resumo`, `GET /perfil/{id}/visualizacoes` — e mídia em `/media/uploads/{arquivo}`.

**Testes validados na Fase 2 (até 13/10/2026):** cadastro→login→perfil do zero (TRUNCATE CASCADE); PUT idempotente (mesmo `id` em 2 chamadas); GET público 200/404/422; upload 201 com uuid no disco; `.txt` → 400; sem token → 401; `/media/...` → 200 `video/mp4` (inclusive com 304 de cache do navegador); `/perfil/1/videos` → 200 com 2 vídeos; `/perfil/999/videos` → 404. **14/10 (estatísticas):** POST 201 com upsert (atualiza em vez de duplicar); `valor: 0` → 422; sem token → 401; lista pública 200 com filtros; `?temporada=1999` → `[]`; `/perfil/999/estatisticas` → 404.

---

*Documento vivo — deve ser atualizado conforme decisões do projeto evoluem.*
