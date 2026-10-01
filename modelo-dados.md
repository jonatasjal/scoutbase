# ScoutBase — Modelo de Dados Refinado (Etapa 0)

**Referente à Seção 10 de `documentacao-projeto.md`**
**Versão 2.0 — incorpora as decisões do plano de execução aprovado**

---

## 1. O que mudou em relação à v1

| Mudança | Motivo |
|---|---|
| Nova entidade `Visualizacao` | Suportar o dashboard de views do atleta sem retrabalho de schema |
| Campo `plano` em `Usuario` | Reservar a lógica freemium/assinatura desde já, mesmo sem cobrança real no MVP |
| `usuario_visitante_id` opcional em `Visualizacao` | Permitir contar visitas anônimas, não só de usuários logados |
| `EstatisticaAtleta` confirmada como genérica (métrica + valor) | Evitar redesenho ao entrar um segundo esporte |
| `ResponsavelLegal` mantida (sem tela no MVP) | É a base de dado que sustenta o "log de consentimento" das mensagens |
| Índices de busca explicitados | A busca com filtros (Fase 3) só é rápida se pensada agora |

Total: **10 entidades** (as 9 originais + `Visualizacao`, com `ResponsavelLegal` reconfirmada como necessária mesmo sem UI própria). O valor `patrocinador` fica reservado no enum `tipo_usuario`, sem entidade própria — não conta na soma.

---

## 2. Entidades

### 2.1 `Usuario`
Conta de login, independente do tipo de perfil.

- `id`
- `email` (único, indexado)
- `senha_hash`
- `tipo_usuario`: enum — `atleta`, `olheiro`, `responsavel`, `patrocinador` (reservado, sem tela na Fase 2/MVP conforme recomendação #1)
- `plano`: enum — `gratuito`, `pago` (default `gratuito`; sem cobrança real implementada no MVP, só o campo)
- `criado_em`

### 2.2 `Atleta`
Dados esportivos, vinculada 1-para-1 a um `Usuario` do tipo `atleta`.

- `id`
- `usuario_id` (FK, único)
- `data_nascimento` — usada para calcular idade e disparar a regra de menor de idade
- `esporte`: enum (só `futebol` habilitado na V1, mas campo já existe para Fase 8)
- `posicao`
- `categoria` (ex: sub-15, sub-17, adulto)
- `cidade`, `estado` (indexados — ver Seção 4)
- `clube_atual`
- `bio`

### 2.3 `ResponsavelLegal`
Vínculo entre um responsável e um atleta menor de idade. **Sem tela de CRUD no MVP**, mas obrigatória no modelo — sem ela não existe o que registrar no log de consentimento (item 2 do plano).

- `id`
- `usuario_id` (FK — o responsável também é um `Usuario`, tipo `responsavel`)
- `atleta_id` (FK)
- `parentesco` (ex: mãe, pai, tutor)
- `vinculo_ativo`: booleano (default `true`)
- `criado_em`

*No MVP, o preenchimento pode ser feito via seed/admin simples — sem formulário dedicado no frontend.*

### 2.4 `VideoAtleta`
- `id`
- `atleta_id` (FK)
- `tipo_origem`: enum — `link_externo` (Fase 2a) ou `arquivo_upload` (logo em seguida, conforme recomendação #5)
- `url_ou_caminho`
- `titulo`
- `tamanho_bytes` (nulo se for link externo; validado contra limite de ~100MB no upload)
- `data_upload`

### 2.5 `EstatisticaAtleta`
Estrutura genérica — confirmada pela recomendação #4.

- `id`
- `atleta_id` (FK)
- `competicao`
- `temporada`
- `metrica`: enum/string (ex: `gols`, `assistencias`, `jogos`, `minutos_jogados` — para futebol; outros esportes adicionam seus próprios valores sem alterar a tabela)
- `valor`: numérico

*O frontend, na Fase 5, agrupa as métricas conhecidas de futebol em uma UI específica (cartões "Gols", "Assistências" etc.), mesmo o dado sendo genérico no banco.*

### 2.6 `Olheiro`
- `id`
- `usuario_id` (FK, único)
- `organizacao`
- `cargo`
- `verificado`: booleano (default `false` — selo de verificação é Fase 2)

### 2.7 `Favorito`
Relação muitos-para-muitos entre `Olheiro` e `Atleta`.

- `id`
- `olheiro_id` (FK)
- `atleta_id` (FK)
- `criado_em`
- *(chave única composta `olheiro_id + atleta_id` — evita duplicar favorito)*

### 2.8 `Mensagem`
- `id`
- `remetente_id` (FK → `Usuario`)
- `destinatario_id` (FK → `Usuario`)
- `conteudo`
- `lida`: booleano
- `criado_em`
- `consentimento_responsavel_id`: FK nula para `ResponsavelLegal` — **preenchida automaticamente quando o destinatário (ou remetente) é um atleta menor de idade**, registrando qual vínculo ativo autorizou o contato (é o "log de consentimento" da recomendação #2)

### 2.9 `Avaliacao` (Fase 2 — mantida no modelo, sem uso no MVP)
- `id`
- `atleta_id` (FK)
- `avaliador_id` (FK)
- `nota`
- `comentario`
- `criado_em`

### 2.10 `Visualizacao` *(nova)*
Suporta o dashboard de views do atleta.

- `id`
- `atleta_id` (FK) — de quem é o perfil visto
- `usuario_visitante_id`: FK **opcional/nula** para `Usuario` — permite registrar visitas de usuários não autenticados (decisão A da conversa anterior)
- `criado_em`

**Como isso resolve "único vs. total" sem retrabalho:**
- **Total de views** = `COUNT(*)` de todas as linhas do atleta
- **Views únicas (entre logados)** = `COUNT(DISTINCT usuario_visitante_id)` onde não é nulo
- **Views anônimas** = `COUNT(*)` onde `usuario_visitante_id` é nulo

Isso dá as duas métricas pedidas na dúvida #3 sem precisar de nenhuma tabela adicional.

---

## 3. Relacionamentos (resumo)

```
Usuario 1---1 Atleta
Usuario 1---1 Olheiro

Usuario 1---N ResponsavelLegal N---1 Atleta
  (tabela de vínculo: um responsável pode gerenciar vários atletas;
   um atleta menor pode ter mais de um responsável ativo)
Atleta 1---N VideoAtleta
Atleta 1---N EstatisticaAtleta
Atleta 1---N Avaliacao
Atleta 1---N Visualizacao

Olheiro N---N Atleta   (via Favorito)
Usuario N---N Usuario  (via Mensagem, remetente/destinatario)
Mensagem N---1 ResponsavelLegal (opcional, só quando envolve menor de idade)
```

---

## 4. Índices de busca recomendados

A Fase 3 (`GET /atletas?esporte=&posicao=&idade=&estado=`) só é rápida se os campos de filtro forem indexados desde a primeira migration:

- Índice em `Atleta.esporte`
- Índice em `Atleta.posicao`
- Índice em `Atleta.estado` (e opcionalmente `cidade`, se o volume de dados crescer)
- Índice em `Atleta.categoria`
- Indexar `Atleta.data_nascimento` e calcular a faixa etária na query — em vez de manter uma coluna `idade` que precisaria ser recalculada (idade muda com o tempo)
- Índice único em `Usuario.email`
- Índice composto único em `Favorito(olheiro_id, atleta_id)`
- Índice composto em `EstatisticaAtleta(atleta_id, competicao, temporada)`
- Índice composto em `Mensagem(remetente_id, destinatario_id)`
- Índice composto em `Visualizacao(atleta_id, criado_em)`

---

## 5. Fluxo da regra de consentimento (LGPD — recomendação #2 detalhada)

1. Um `Atleta` é cadastrado. O backend calcula a idade a partir de `data_nascimento`.
2. Se idade < 18, o sistema **exige** que exista pelo menos um `ResponsavelLegal` com `vinculo_ativo = true` associado a esse atleta antes de permitir que o perfil fique visível na busca pública.
3. Quando qualquer `Mensagem` é criada envolvendo esse atleta (como remetente ou destinatário), o backend:
   - Verifica se o atleta é menor de idade
   - Se for, busca o `ResponsavelLegal` com vínculo ativo
   - Preenche `Mensagem.consentimento_responsavel_id` com essa referência
   - Se não houver responsável ativo, a mensagem é bloqueada (regra de negócio testável via Pytest, como já previsto na Etapa D)

Isso cumpre o "log de consentimento" sem exigir nenhuma tela de responsável no MVP — é uma regra de backend, não uma feature de UI.

---

## 6. Resumo das 10 entidades

1. Usuario
2. Atleta
3. ResponsavelLegal
4. VideoAtleta
5. EstatisticaAtleta
6. Olheiro
7. Favorito
8. Mensagem
9. Avaliacao
10. Visualizacao

*(reservado, fora da contagem)* — o enum `tipo_usuario` inclui `patrocinador` sem entidade própria no MVP; quando a Fase 2 implementar o perfil de patrocinador, uma entidade `Patrocinador` (espelhando `Olheiro`) será adicionada. O espaço no enum já está reservado.

---

## 7. Próximo passo

Com este modelo aprovado, a Etapa 0 segue para:
- `git init` + `.gitignore`
- Estrutura de pastas (`backend/`, `frontend/`, `docker-compose.yml`)
- Primeira migration criando as 10 tabelas (Patrocinador continua só como valor de enum, sem entidade)
