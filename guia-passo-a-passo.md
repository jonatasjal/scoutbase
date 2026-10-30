# 📖 Guia Passo a Passo — ScoutBase

> Este documento guarda **todas as explicações didáticas** das fases do projeto, na ordem em que foram feitas.
> Cada nova fase/etapa será acrescentada aqui no final.
>
> **Como usar:** siga os passos na ordem, execute os comandos no PowerShell e só avance quando o checkpoint der certo.

---

## 🪪 Cartão de teste (consulte sempre que precisar)

| Campo | Valor |
|---|---|
| E-mail | `joao@email.com` |
| Senha | `senha123` |
| Tipo | atleta (usuario id 1, atleta id 1) |
| Token JWT | **expira em 60 min** — se der 401, refaça `POST /auth/login` para gerar um novo (copie da resposta em `access_token`) |

> Os dados existem **no banco** (tabelas `usuario` e `atleta`). Se o banco for zerado, refaça o cadastro no Swagger (`POST /auth/cadastro`). Como consultar pelo terminal:
> ```powershell
> docker exec scoutbase-db psql -U scoutbase -d scoutbase -c "SELECT id, email, tipo_usuario FROM usuario;"
> ```

---

# 🚀 Fase 0 — Fundamentos e ambiente

**Objetivo da fase:**
1. Definir e documentar o modelo de dados final (entidades e relacionamentos) ✅
2. Configurar o ambiente local: estrutura de pastas do backend e do frontend
3. Configurar o banco de dados PostgreSQL localmente (via Docker)
4. Criar a primeira migração de banco (criar as tabelas a partir do modelo de dados)

---

## Passo 1 — Modelo de dados documentado ✅

O item 1 da fase é documentação, e já existe:
- `documentacao-projeto.md` — visão de produto, requisitos, roadmap
- `modelo-dados.md` — as 10 entidades e relacionamentos

**Sua tarefa:** leia o `modelo-dados.md` (seção 2 — as 10 entidades). Ele é a **fonte da verdade** para tudo que vamos criar.

### Pergunta de verificação (responda para você):

> *"Se eu quiser saber quantos vídeos um atleta tem, de qual entidade eu parto?"*
>
> **Resposta:** `VideoAtleta` → FK `atleta_id` (cada linha de `VideoAtleta` é um vídeo; contando as linhas com aquele `atleta_id`, você sabe quantos vídeos o atleta tem).

---

## Passo 2 — Estrutura de pastas

### Comandos para executar no PowerShell

```powershell
cd C:\Users\jonat\Desktop\ScoutBase
mkdir backend, frontend
mkdir backend\app, backend\tests, backend\alembic\versions, backend\media\uploads
mkdir frontend\src, frontend\public
```

### O que cada pasta é

| Pasta | Função |
|---|---|
| `backend\app` | código da API (futuro: models, routes, services) |
| `backend\alembic\versions` | migrations (SQL gerado pelo código) |
| `backend\tests` | testes automatizados |
| `backend\media\uploads` | vídeos enviados |
| `frontend\src` | código React (Fase 4) |

**Por que já criar a estrutura do frontend se ele só vem na Fase 4?**
Porque o documento raiz (README + organização) precisa refletir o projeto inteiro desde o início. Criar pastas vazias é grátis e evita bagunça depois.

### Inicializar o Git

```powershell
git init
notepad .gitignore
```

No bloco que abrir, cole e **salve** (Ctrl+S):

```
.env
__pycache__/
*.pyc
.venv/
node_modules/
pgdata/
backend/media/uploads/*
!backend/media/uploads/.gitkeep
```

**Por que existe um `.gitignore`?**
O Git versiona tudo que está na pasta — inclusive arquivos que **não devem** virar histórico:
- `.env` → contém senhas; se subir pro repositório, vaza
- `__pycache__/`, `.venv/`, `node_modules/` → arquivos gerados automaticamente, milhões deles
- `backend/media/uploads/*` → vídeos pesados demais pro Git

Crie também o marcador de pasta vazia:

```powershell
New-Item -ItemType File backend\media\uploads\.gitkeep
```

> **Por que o `.gitkeep`?** O Git **não guarda pastas vazias** (só guarda arquivos). Colocar um arquivo vazio `.gitkeep` é um truque universal para forçar o Git a manter a pasta `uploads` no repositório. A linha `!backend/media/uploads/.gitkeep` no `.gitignore` garante que esse marcador seja a **única** coisa que sobreviva dentro da pasta.

---

## Passo 3 — PostgreSQL via Docker 🐘

### 3.1 — Primeiro, o problema que estamos resolvendo

O projeto **ScoutBase** precisa guardar dados permanentemente: usuários, atletas, vídeos, favoritos...

Para isso existe o **PostgreSQL** (o "Postgres"): um *banco de dados* — um programa que organiza tudo em **tabelas** (como abas de uma planilha), com linhas, colunas e relacionamentos, e que **não perde os dados** quando você desliga o computador.

#### Por que não simplesmente instalar o Postgres no Windows?

Você *poderia*. Mas seria ruim assim:

| Problema | O que acontece |
|---|---|
| **Sujeira no PC** | Instalação modifica registro do Windows, cria serviços, variáveis de ambiente |
| **Conflito de versões** | Hoje você quer Postgres 16; amanhã outro projeto quer 12 — dá briga |
| **Difícil de desfazer** | Desinstalar sempre deixa "restos" pra trás |
| **Diferença entre máquinas** | Funciona no seu PC, quebra no PC do colega/cliente |

### 3.2 — O que é Docker (a ideia central)

O Docker é uma ferramenta que empacota um programa **junto com todo o ambiente dele** numa caixa isolada chamada **container**.

> **Analogia:** em vez de cozinhar na sua cozinha (instalar Postgres no Windows), você usa uma **cozinha industrial selada** (container) que já vem com fogão, panelas e ingredientes — ela sobe pronta, faz o trabalho e você desliga sem sujar sua cozinha.

No nosso `docker-compose.yml` dizemos: *"quero a caixa com o Postgres 16 dentro"* — o Docker baixa essa imagem da internet e roda.

**Vantagens concretas pro projeto:**
1. **Reprodutível** — qualquer pessoa com o arquivo `docker-compose.yml` sobe o mesmo banco, igualzinho
2. **Descartável** — `docker compose down -v` apaga TUDO sem deixar rastro no Windows
3. **Isolado** — só afeta o container, nunca seu PC

### 3.3 — O que é o docker-compose e por que YAML

O Docker puro você comandaria com vários `docker run ...` (feio e difícil de lembrar).

O **Compose** é um "atalho": você descreve seus serviços **uma vez** num arquivo `docker-compose.yml` e depois usa comandos curtos:

| Comando | Significado |
|---|---|
| `docker compose up -d db` | Suba o serviço chamado `db` |
| `docker compose ps` | Quais serviços estão rodando? |
| `docker compose down` | Desligue os serviços |
| `docker compose down -v` | Desligue **e apague os dados** (o volume) |

> **YAML** é só um formato de arquivo de texto estruturado (usa espaços, com `:` e `-`). É o padrão do mundo para configs.

**Por que `db` e não `database`?** Pura conveniência: na documentação o serviço já se chama `db`. Nome curto = menos erro de digitação.

### 3.4 — Análise linha por linha do arquivo

```yaml
services:
```
> Raiz do Compose. Aqui dentro ficam os programas que vão rodar. Podem ser vários (ex: `db` + `redis`); nós teremos só o `db` por enquanto.

```yaml
  db:
    image: postgres:16-alpine
```
> **Qual imagem usar.** `postgres` = o banco oficial. `16` = a versão (a mais estável hoje). `alpine` = build mínimo baseado em Alpine Linux — ocupa ~240MB (o normal passa de 400MB). Função idêntica, só mais leve.

```yaml
    container_name: scoutbase-db
```
> **Nome fixo do container.** Sem isso o Docker geraria nomes aleatórios (`scoutbase-db-xyz123`). Com nome fixo, dá pra rodar `docker logs scoutbase-db` depois.

```yaml
    restart: unless-stopped
```
> **Comportamento ao reiniciar o PC.** Se o Docker Desktop iniciar com o Windows, o banco volta sozinho. E se o Postgres travar, o Docker tenta religar automaticamente. Você nunca fica sem banco por esquecer.

```yaml
    environment:
      POSTGRES_USER: scoutbase
      POSTGRES_PASSWORD: scoutbase
      POSTGRES_DB: scoutbase
```
> **Variáveis de ambiente** — são as configurações passadas *para dentro* da caixa, no momento em que ela sobe. O Postgres lê essas 3:
> - `POSTGRES_USER` — nome do usuário/administrador
> - `POSTGRES_PASSWORD` — a senha dele
> - `POSTGRES_DB` — qual banco de dados criar automaticamente ao iniciar
>
> ⚠️ **Regra de ouro:** essas credenciais são **fixas e previsíveis de propósito** porque é ambiente de desenvolvimento local (só existe no SEU PC). Em produção (mais tarde), isso vira variáveis de ambiente secretas — nunca hardcoded.

```yaml
    ports:
      - "5432:5432"
```
> **Abre a porta.** Ponto crítico de entender:
> - O Postgres *dentro* da caixa fala sempre na porta `5432` (padrão do mundo inteiro)
> - Mas ele está isolado — seu PC não consegue alcançá-lo
> - O formato `5432:5432` significa: **"porta do seu PC" : "porta do container"**
>
> Resultado: quando o seu backend (que roda FORA do Docker) escrever `localhost:5432`, o Docker **encaminha** o pedido para dentro da caixa. É como um porteiro do prédio.

```yaml
    volumes:
      - pgdata:/var/lib/postgresql/data
```
> **O DISCO RÍGIDO do container.** Ponto crítico:
>
> Container = **efêmero**. Se você apagar o container e subir outro, TODO o conteúdo interno some — porque o container é descartável por natureza.
>
> Mas o Postgres grava seus dados em `/var/lib/postgresql/data` (dentro da caixa). Se isso morrer com o container, você perde usuários, atletas... tudo.
>
> A solução: **volume**. O formato `pgdata:/var/lib/...` diz:
> - `pgdata` → nome de um volume (área de disco gerenciada pelo Docker, **fora** do container)
> - `/var/lib/postgresql/data` → pasta de dentro onde ele será "montado" (como um HD externo plugado)
>
> Agora o container pode morrer e nascer quantas vezes quiser — **os dados continuam no volume `pgdata`**.
> Só o comando especial `docker compose down -v` (com o `-v`) apaga o volume propositalmente.

```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U scoutbase -d scoutbase"]
      interval: 10s
      timeout: 5s
      retries: 5
```
> **Sondagem de vida.** Todo container tem status `running` logo que inicia — mas isso **não significa que o serviço está pronto**. O Postgres demora alguns segundos para aceitar conexões.
>
> O Docker, a cada 10 segundos, executa *dentro* do container: `pg_isready` (ferramenta do próprio Postgres = "está aceitando conexões?"). Se não responder em 5s, tenta de novo — 5 falhas seguidas = `unhealthy`.
>
> Para o uso atual, serve para ver `healthy` no `docker compose ps` = "meu banco está realmente pronto". Mais à frente, testes automatizados vão esperar esse `healthy` antes de rodar (evita erro "banco não conecta" logo ao subir).

```yaml
volumes:
  pgdata:
```
> **Declaração do volume** na raiz. É só burocracia de YAML: o volume `pgdata` tem que ser *declarado* aqui para o Docker criar com nome previsível (senão ele gera nome aleatório e fica difícil achar/deletar).

### Arquivo final — `docker-compose.yml` (com comentários)

> Os `#` são ignorados pelo Docker — o comportamento é idêntico. A vantagem é que,
> meses depois, você abre o arquivo e já sabe o *porquê* de cada linha.

```yaml
# ===================================================================
# ScoutBase — docker-compose.yml
# Descreve os serviços (programas) do projeto rodando em containers.
#
# Como usar:
#   docker compose up -d db   -> sobe o banco em 2º plano
#   docker compose ps         -> mostra status (esperar "healthy")
#   docker compose down       -> desliga, MANTÉM os dados
#   docker compose down -v    -> desliga e APAGA os dados (volume)
# ===================================================================

services:                          # raiz do Compose: aqui ficam os programas

  db:                              # nome curto do serviço (usado nos comandos)
    image: postgres:16-alpine      # imagem oficial do Postgres 16; alpine = versão leve (~240MB)
    container_name: scoutbase-db   # nome fixo do container (para logs: docker logs scoutbase-db)
    restart: unless-stopped        # religa sozinho se travar ou se o PC reiniciar

    # --- Credenciais lidas pelo Postgres na primeira subida -------------
    environment:
      POSTGRES_USER: scoutbase       # usuário administrador criado automaticamente
      POSTGRES_PASSWORD: scoutbase   # senha dele (ok em dev local; em produção seria secreta)
      POSTGRES_DB: scoutbase         # banco criado automaticamente ao iniciar

    # --- Encaminhamento de porta ----------------------------------------
    ports:
      - "5432:5432"                # "porta do seu PC" : "porta do container"
                                   # localhost:5432 fora = 5432 dentro (o porteiro do prédio)

    # --- Volume = "HD externo" do container ------------------------------
    volumes:
      - pgdata:/var/lib/postgresql/data   # volume "pgdata" montado na pasta de dados do Postgres
                                          # dados sobrevivem mesmo se o container for apagado
                                          # (só "down -v" apaga este volume)

    # --- Healthcheck: "rodando" não é o mesmo que "pronto" --------------
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U scoutbase -d scoutbase"]  # pergunta ao Postgres: "aceita conexão?"
      interval: 10s               # testa a cada 10 segundos
      timeout: 5s                 # dá 5s para responder
      retries: 5                  # 5 falhas seguidas = status "unhealthy"

# --- Declaração do volume (obrigatória no YAML) -------------------------
volumes:
  pgdata:                         # nome previsível do volume (senão o Docker gera um aleatório)
```

### 3.5 — Os comandos e o que acontece por dentro

#### `docker compose up -d db`
1. Procura o `docker-compose.yml` **no diretório atual** (por isso o `cd` é obrigatório)
2. Baixa a imagem `postgres:16-alpine` (só na primeira vez; depois fica em cache)
3. Cria o volume `pgdata`
4. Cria e **inicia** o container
5. `-d` = *detached* = roda em **segundo plano** (sem prender seu terminal)

#### `docker compose ps`
Lista os containers deste projeto + status. Você deve ver `Up` e `healthy`.

#### `docker compose exec db psql -U scoutbase -d scoutbase -c "SELECT 1;"`

Fatiando esse comando:

| Parte | O que faz |
|---|---|
| `exec` | "Execute um comando **dentro** do container rodando" |
| `db` | ...container do serviço `db` |
| `psql` | ferramenta de linha de comando do Postgres (falar SQL direto) |
| `-U scoutbase` | usuário: `scoutbase` |
| `-d scoutbase` | banco: `scoutbase` |
| `-c "SELECT 1;"` | execute esse SQL e saia |

O `SELECT 1;` é o "hello world" do SQL — não retorna nada útil, só prova que **a cadeia inteira funciona**: seu terminal → porta 5432 → Docker → container → Postgres → banco `scoutbase`. Se aparecer `1`, tudo conectou.

### 3.6 — Erros comuns e como resolver

| Erro | Causa | Correção |
|---|---|---|
| `docker: command not found` | Shell aberto antes do Docker instalar | Feche e abra um **novo** PowerShell |
| `error during connect: ... daemon not running` | Docker Desktop fechou | Abra o **Docker Desktop** (ícone baleia) e espere o ícone ficar verde |
| `no configuration file provided` | Você está fora da pasta do projeto | `cd C:\Users\jonat\Desktop\ScoutBase` antes |
| `port is already allocated` | Outro serviço usa a 5432 | Peça ajuda para resolver |
| `psql: ... connection ... No such file or directory` | Comando rodou **antes do Postgres terminar de iniciar** (na 1ª subida o `initdb` leva 5-15s) | Esperar o status mudar de `(health: starting)` para `(healthy)` e rodar de novo: `docker compose ps` → repetir o `psql` |

> 📌 **Lição prática (vivida no Passo 3):** container `Up` ≠ serviço pronto.
> O `healthcheck` existe exatamente para isso — ver `(healthy)` antes de conectar.

### ✅ Checkpoint do Passo 3

```powershell
cd C:\Users\jonat\Desktop\ScoutBase
notepad docker-compose.yml
```
Cole o conteúdo YAML acima, **salve** (Ctrl+S) e feche.

```powershell
docker compose up -d db
docker compose ps
docker compose exec db psql -U scoutbase -d scoutbase -c "SELECT 1;"
```

Se aparecer `1`, o Passo 3 está concluído → Parta para o Passo 4.

---

## Passo 4 — Primeira migração (criar as tabelas)

### 4.0 — O conceito central: o que é uma "migration"?

O banco de dados vai **evoluir ao longo do projeto**: hoje 10 tabelas; amanhã uma coluna nova; depois uma tabela inteira. Como fazer isso **sem perder dados e sem quebrar o sistema que já está no ar?**

> **Analogia do Git:** com o Git, você versiona seu **código** — cada mudança vira um commit, dá pra voltar no tempo, dá pra reproduzir em outra máquina.
>
> A **migration** é a mesma coisa, mas pro **banco de dados**: cada mudança de estrutura vira um **arquivo versionado**.

Uma migration é um arquivo Python com dois métodos:

| Método | Função |
|---|---|
| `upgrade()` | **Aplica** a mudança (ex: `CREATE TABLE usuario...`) |
| `downgrade()` | **Desfaz** a mudança (ex: `DROP TABLE usuario...`) |

Quem gera esse arquivo? O **Alembic** — a ferramenta de migrations do ecossistema Python/SQLAlchemy.

#### O fluxo completo

```
modelo-dados.md (sua documentação)
       ↓  você transcreve para
models SQLAlchemy (classes Python = tabelas)
       ↓  Alembic compara models × banco e GERA
arquivo de migration (SQL versionado)
       ↓  você aplica com
Postgres (tabelas criadas)
```

Por que não digitar SQL à mão? Porque **o código Python vira fonte da verdade**: se você alterar a model, o Alembic detecta a diferença e gera a migration seguinte automaticamente.

---

### 4.1 — `requirements.txt` (as dependências)

Em vez de instalar bibliotecas uma por uma e esquecer o que usou, criamos um **manifesto**: lista de tudo que o projeto precisa, com versão fixada.

```powershell
cd C:\Users\jonat\Desktop\ScoutBase\backend
notepad requirements.txt
```

```txt
# Framework web: monta a API (rotas, validação automática, /docs interativo)
fastapi==0.115.6

# Servidor que roda a API e recebe as requisições HTTP
uvicorn[standard]==0.34.0

# ORM: mapeia tabelas do banco para classes Python
# (escrevemos Python, ele traduz para SQL)
sqlalchemy==2.0.36

# Driver de conexão: a "ponte" entre Python e o Postgres
psycopg2-binary==2.9.10

# Alembic: gera e aplica as migrations (versionamento do banco)
alembic==1.14.0

# Lê configurações do arquivo .env (senhas, URLs)
pydantic-settings==2.7.0
```

**Por que `==` com a versão?** Reprodutibilidade. Sem o `==`, amanhã o pip baixa uma versão nova que pode ter mudado comportamento e o projeto "magicamente" quebra. Com versão fixada, o resultado é **sempre o mesmo**.

**O que cada pacote faz na prática:**

| Pacote | Papel no ScoutBase |
|---|---|
| `fastapi` | Define os endpoints (`/perfil`, `/atletas`...) e valida dados |
| `uvicorn` | Fica ouvindo a porta 8000 e entrega as requisições pro FastAPI |
| `sqlalchemy` | Faz `Atleta(...)` virar `INSERT INTO atleta...` |
| `psycopg2` | Consegue falar com o Postgres de verdade |
| `alembic` | Criará as 10 tabelas |
| `pydantic-settings` | Lê a URL do banco do `.env` (nunca hardcoded no código) |

---

### 4.2 — Ambiente virtual (`.venv`)

Seu PC tem **um** Python instalado, mas cada projeto precisa de **suas** bibliotecas com **suas** versões. Sem isolamento, tudo iria pro Python global: projeto A pede SQLAlchemy 1.0, projeto B pede 2.0 — conflito.

> **Analogia:** o `.venv` é uma **mochila por projeto**. Cada projeto carrega as bibliotecas dele na mochila dele. Não mistura, não vaza pro computador inteiro.

`python -m venv .venv` cria em `backend\.venv\`:
- uma **cópia** do executável do Python
- uma **pasta de bibliotecas própria**
- um **activator** que troca qual Python o terminal usa

---

### 4.3 — Criar a mochila e instalar tudo

```powershell
# Confirme que tem Python 3.12+
python --version

# Crie o ambiente virtual (pasta .venv dentro de backend\)
python -m venv .venv

# Atualize o instalador de pacotes (boas práticas)
.\.venv\Scripts\python.exe -m pip install --upgrade pip

# Instale TUDO do requirements.txt dentro da mochila
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> **Nota didática:** o comando de ativação tradicional é `.\.venv\Scripts\Activate.ps1`, mas ele às vezes é bloqueado pela política de execução do PowerShell. Usar o caminho direto `.\.venv\Scripts\python.exe` tem o **mesmo efeito** e nunca dá erro.

**Verificação:** `Successfully installed...` sem mensagens de erro.

---

### 4.4 — Esqueleto do backend

#### Estrutura

```
backend\
├── requirements.txt   ✅
├── .env               ← credenciais (git ignorado!)
├── .venv\             ✅ (mochila)
└── app\
    ├── __init__.py    ← marca "isto é um pacote Python"
    ├── config.py      ← lê o .env
    ├── database.py    ← engine + sessões + Base
    └── main.py        ← entrada da API (porta 8000)
```

#### Por que 4 arquivos separados?

| Arquivo | Responsabilidade | Por que separar? |
|---|---|---|
| `config.py` | **Saber as configurações** (URL do banco) | Se mudar a senha, mexe em 1 lugar só |
| `database.py` | **Conectar no banco** (engine, sessões) | Todas as models herdam da `Base` daqui — ponto único |
| `main.py` | **Receber requisições** (rotas HTTP) | Quem fala com o mundo externo não mistura com quem fala com o banco |

#### Comandos

```powershell
cd C:\Users\jonat\Desktop\ScoutBase\backend
mkdir app
notepad app\__init__.py      # deixe vazio, salve e feche
```

#### 📄 `.env` — o arquivo de segredos

```powershell
notepad .env
```

```env
DATABASE_URL=postgresql+psycopg2://scoutbase:scoutbase@localhost:5432/scoutbase
```

**Anatomia da URL:**
```
postgresql+psycopg2://  usuário : senha @ localhost : 5432 / banco
└── esquema + driver ┘   └─ credenciais do docker-compose ─┘  └ nome do DB ┘
```

> **Por que num arquivo separado?** Porque o `.gitignore` **bloqueia o `.env`**. Seu código vai pro GitHub; sua senha **não**.

#### 📄 `app\config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://scoutbase:scoutbase@localhost:5432/scoutbase"
    model_config = {"env_file": ".env"}


settings = Settings()
```

A classe `Settings` lê variáveis do `.env` e as expõe como atributos (`settings.database_url`). O valor default é rede de segurança: se o `.env` faltar, ainda funciona em dev.

#### 📄 `app\database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass
```

| Objeto | Papel |
|---|---|
| `engine` | A **fábrica de conexões** — gerencia o "fio" com o Postgres |
| `SessionLocal` | Uma **sessão** = 1 conexão de trabalho (usada em cada requisição) |
| `Base` | Classe **mãe** de todas as models. O Alembic olha `Base.metadata` e descobre **quais tabelas existem** |

#### 📄 `app\main.py`

```python
from fastapi import FastAPI

app = FastAPI(title="ScoutBase API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}
```

A **menor API possível** — uma rota `GET /health` que responde "estou vivo". Se `/health` responde, o esqueleto (Python + FastAPI + uvicorn) funciona.

---

### 4.5 — Subir e testar

Aba **nova** no PowerShell (servidor):

```powershell
cd C:\Users\jonat\Desktop\ScoutBase\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

> `--reload` = recarrega sozinho a cada arquivo salvo.

Outra aba (cliente):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

**Saída esperada:**

```
status
------
ok
```

Diferencial FastAPI: abra **http://127.0.0.1:8000/docs** no navegador → interface interativa com `/health` documentada automaticamente.

---

### ✅ Checkpoint do Passo 4 — 4.5 CONCLUÍDO (25/09/2026)

- `pip install` → `Successfully installed` (26 pacotes)
- `uvicorn app.main:app --reload` → `Application startup complete.`
- `GET /health` → `{"status": "ok"}`

Próxima subetapa: **Alembic + as 10 models** (as tabelas do `modelo-dados.md` viram código).

---

### 4.6 — Alembic: o "Git do banco de dados"

#### O que é

O Alembic é a ferramenta de migrations do Python. Comandos principais:

| Comando | O que faz |
|---|---|
| `alembic init alembic` | Cria a estrutura de configuração (só 1 vez) |
| `alembic revision --autogenerate` | **Compara** models × banco e **gera** um novo arquivo de migration |
| `alembic upgrade head` | **Aplica** a migration pendente no banco |
| `alembic current` | Que versão o banco está? |
| `alembic history` | Linha do tempo de todas as migrations |

#### O que o `init` cria

```
backend\
├── alembic.ini          ← configuração geral (onde fica o script_location)
└── alembic\
    ├── env.py           ← a "ponte": diz ao Alembic qual URL usar e quais models olhar
    ├── script.py.mako   ← template dos novos arquivos de migration
    └── versions\        ← ⭐ AQUI ficam os arquivos de migration gerados
```

#### Comandos

```powershell
cd C:\Users\jonat\Desktop\ScoutBase\backend

# A pasta alembic/ já existe (vazia, do Passo 2) e o init recusa pasta não vazia
Remove-Item -Recurse alembic

# Cria a estrutura oficial
.\.venv\Scripts\python.exe -m alembic init alembic
```

> **Por que `-m alembic`?** Porque o Alembic está instalado **dentro da mochila** `.venv` — usar `python -m pacote` executa o módulo com o Python certo, sem depender de ativação.

#### Configurar a ponte — `alembic\env.py`

Substitua **todo o conteúdo** do arquivo pelo abaixo:

```python
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.config import settings
from app.database import Base

config = context.config

# 1) URL do banco vem do .env (fonte única de verdade — não digite senha aqui)
config.set_main_option("sqlalchemy.url", settings.database_url)

# 2) Sistema de logs do próprio Alembic
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3) O catálogo: Base.metadata = TODAS as models declaradas até hoje.
#    O Alembic compara este catálogo × tabelas reais → diferença = nova migration
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Modo offline: gera o SQL sem conectar no banco."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo online: conecta no banco e executa as mudanças."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**As 3 ligações que tornam isso possível:**

| Linha | Liga o quê |
|---|---|
| `from app.config import settings` | Alembic ← seu `.env` (URL do banco) |
| `from app.database import Base` | Alembic ← suas models futuras |
| `target_metadata = Base.metadata` | **O coração**: o catálogo que o Alembic compara com o banco |

> Você **não** precisa editar o `alembic.ini` — a linha `sqlalchemy.url` dele é sobrescrita em tempo de execução pelo `env.py` (o `.env` manda).

#### Verificação

```powershell
.\.venv\Scripts\python.exe -m alembic history
```

**Saída esperada: NENHUMA (terminal volta limpo).** ✅

> Verificado na prática (25/09/2026): com a pasta `versions/` vazia, o `alembic history`
> do 1.14.0 imprime **nada** e sai com código 0. `heads` idem. O silêncio = sucesso.
> Erro de verdade aparece como `FAILED: No config file 'alembic.ini' found...`.
> O teste real da ponte `env.py` virá no 4.8 (autogenerate lê o banco).

---

### 4.7 — As 10 models (`modelo-dados.md` → Python)

#### Onde vive o código

**Um único arquivo:** `backend\app\models.py`. As 10 entidades na mesma ordem do
documento — depois (fases avançadas) pode virar uma pasta `models/` dividida.

#### A tradução — cada entidade = 1 classe = 1 tabela

| `modelo-dados.md` diz | Código (SQLAlchemy 2.0) | Postgres |
|---|---|---|
| `id` | `Mapped[int] = mapped_column(primary_key=True)` | `INTEGER PRIMARY KEY` |
| `usuario_id` (FK, único) | `mapped_column(ForeignKey("usuario.id"), unique=True)` | `INT REFERENCES usuario(id) UNIQUE` |
| campo indexado | `index=True` | `CREATE INDEX` |
| booleano default true | `mapped_column(Boolean, default=True)` | `BOOLEAN DEFAULT TRUE` |
| datetime de criação | `mapped_column(DateTime, server_default=func.now())` | `DEFAULT now()` (o **banco** marca a hora) |

#### Dois conceitos novos

**1. `Mapped[...]` + `mapped_column(...)`** — anotação de tipo + schema, o padrão
oficial do SQLAlchemy 2.0. `Mapped[str | None]` (com `| None`) vira `NULLABLE`
automaticamente.

**2. Enums = menu fechado.** `tipo_usuario` aceita só 4 valores, não qualquer texto.
Viram **tipos nativos** do Postgres (`CREATE TYPE tipo_usuario AS ENUM (...)`) — o
banco barra dado inválido na entrada. O valor `patrocinador` fica reservado no enum
sem entidade (conforme `modelo-dados.md`).

#### Índices (Seção 4 do modelo — pensados ANTES da Fase 3 existir)

| Índice | Por quê |
|---|---|
| `esporte`, `posicao`, `estado`, `categoria`, `data_nascimento` (Atleta) | Filtros da busca `GET /atletas?...` |
| `email` único (Usuario) | Login rápido + barra duplicidade |
| composto `Favorito(olheiro_id, atleta_id)` UNIQUE | Barra favorito repetido |
| composto `EstatisticaAtleta(atleta_id, competicao, temporada)` | Painel de estatísticas |
| composto `Mensagem(remetente_id, destinatario_id)` | Caixa de mensagens |
| composto `Visualizacao(atleta_id, criado_em)` | Dashboard de views |
| `data_nascimento` em vez de coluna `idade` | Idade envelhece sozinha; recalculada na query |

#### Arquivo completo — `backend\app\models.py`

```python
"""As 10 entidades do ScoutBase — fonte da verdade: modelo-dados.md."""

import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ---------------------------------------------------------------------------
# Enums — "menu fechado"; viram CREATE TYPE nativo no Postgres
# ---------------------------------------------------------------------------

class TipoUsuario(str, enum.Enum):
    atleta = "atleta"
    olheiro = "olheiro"
    responsavel = "responsavel"
    patrocinador = "patrocinador"  # reservado — sem tela no MVP


class Plano(str, enum.Enum):
    gratuito = "gratuito"
    pago = "pago"


class Esporte(str, enum.Enum):
    futebol = "futebol"  # único habilitado na V1; pronto p/ Fase 8


class TipoOrigemVideo(str, enum.Enum):
    link_externo = "link_externo"
    arquivo_upload = "arquivo_upload"


# ---------------------------------------------------------------------------
# 1. Usuario — conta de login, independente do perfil
# ---------------------------------------------------------------------------

class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    tipo_usuario: Mapped[TipoUsuario] = mapped_column(
        Enum(TipoUsuario, name="tipo_usuario"), default=TipoUsuario.atleta
    )
    plano: Mapped[Plano] = mapped_column(
        Enum(Plano, name="plano"), default=Plano.gratuito
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# 2. Atleta — dados esportivos, 1-1 com Usuario do tipo "atleta"
# ---------------------------------------------------------------------------

class Atleta(Base):
    __tablename__ = "atleta"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    data_nascimento: Mapped[date] = mapped_column(Date, index=True)
    esporte: Mapped[Esporte] = mapped_column(
        Enum(Esporte, name="esporte"), default=Esporte.futebol, index=True
    )
    posicao: Mapped[str] = mapped_column(String(50), index=True)
    categoria: Mapped[str] = mapped_column(String(30), index=True)  # sub-15, sub-17...
    cidade: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(2), index=True)
    clube_atual: Mapped[str | None] = mapped_column(String(100))
    bio: Mapped[str | None] = mapped_column(Text)


# ---------------------------------------------------------------------------
# 3. ResponsavelLegal — vínculo responsável × atleta menor (base do log LGPD)
# ---------------------------------------------------------------------------

class ResponsavelLegal(Base):
    __tablename__ = "responsavel_legal"
    __table_args__ = (
        Index("ix_resp_legal_atleta_vinculo", "atleta_id", "vinculo_ativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"))
    parentesco: Mapped[str] = mapped_column(String(30))  # mãe, pai, tutor
    vinculo_ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# 4. VideoAtleta — link externo ou arquivo enviado
# ---------------------------------------------------------------------------

class VideoAtleta(Base):
    __tablename__ = "video_atleta"

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"), index=True)
    tipo_origem: Mapped[TipoOrigemVideo] = mapped_column(
        Enum(TipoOrigemVideo, name="tipo_origem_video"),
        default=TipoOrigemVideo.link_externo,
    )
    url_ou_caminho: Mapped[str] = mapped_column(String(500))
    titulo: Mapped[str] = mapped_column(String(200))
    tamanho_bytes: Mapped[int | None] = mapped_column(BigInteger)  # nulo se link
    data_upload: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# 5. EstatisticaAtleta — genérica (métrica + valor), suporta qualquer esporte
# ---------------------------------------------------------------------------

class EstatisticaAtleta(Base):
    __tablename__ = "estatistica_atleta"
    __table_args__ = (
        Index("ix_estat_comp", "atleta_id", "competicao", "temporada"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"))
    competicao: Mapped[str] = mapped_column(String(100))
    temporada: Mapped[str] = mapped_column(String(10))  # ex: "2026"
    metrica: Mapped[str] = mapped_column(String(50))  # gols, assistencias, jogos...
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))


# ---------------------------------------------------------------------------
# 6. Olheiro — perfil profissional ligado a um Usuario
# ---------------------------------------------------------------------------

class Olheiro(Base):
    __tablename__ = "olheiro"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    organizacao: Mapped[str | None] = mapped_column(String(100))
    cargo: Mapped[str | None] = mapped_column(String(50))
    verificado: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------------------------------------------------------------------------
# 7. Favorito — N×N Olheiro × Atleta (chave única composta)
# ---------------------------------------------------------------------------

class Favorito(Base):
    __tablename__ = "favorito"
    __table_args__ = (
        UniqueConstraint("olheiro_id", "atleta_id", name="uq_favorito_olheiro_atleta"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    olheiro_id: Mapped[int] = mapped_column(ForeignKey("olheiro.id"))
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# 8. Mensagem — + log de consentimento LGPD (FK nula)
# ---------------------------------------------------------------------------

class Mensagem(Base):
    __tablename__ = "mensagem"
    __table_args__ = (
        Index("ix_mensagem_remetente_destinatario", "remetente_id", "destinatario_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    remetente_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    destinatario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    conteudo: Mapped[str] = mapped_column(Text)
    lida: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # preenchida automaticamente quando envolve atleta menor de idade (LGPD)
    consentimento_responsavel_id: Mapped[int | None] = mapped_column(
        ForeignKey("responsavel_legal.id")
    )


# ---------------------------------------------------------------------------
# 9. Avaliacao — no modelo desde já; uso previsto na Fase 2
# ---------------------------------------------------------------------------

class Avaliacao(Base):
    __tablename__ = "avaliacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"), index=True)
    avaliador_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    nota: Mapped[Decimal] = mapped_column(Numeric(3, 1))
    comentario: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# 10. Visualizacao — dashboard de views (total / únicas / anônimas)
# ---------------------------------------------------------------------------

class Visualizacao(Base):
    __tablename__ = "visualizacao"
    __table_args__ = (
        Index("ix_visualizacao_atleta_criado", "atleta_id", "criado_em"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"))
    usuario_visitante_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

#### Ligação extra no `alembic\env.py`

O Alembic só enxerga as models que foram **importadas**. Adicione 1 linha logo abaixo
do `from app.database import Base`:

```python
from app.database import Base
from app import models  # registra as 10 models no Base.metadata
```

#### Checkpoint 4.7 — o catálogo existe?

```powershell
cd C:\Users\jonat\Desktop\ScoutBase\backend
.\.venv\Scripts\python.exe -c "from app import models; from app.database import Base; print(len(Base.metadata.tables), 'tabelas'); print(sorted(Base.metadata.tables))"
```

**Esperado:**

```
10 tabelas
['atleta', 'avaliacao', 'estatistica_atleta', 'favorito', 'mensagem',
 'olheiro', 'responsavel_legal', 'usuario', 'video_atleta', 'visualizacao']
```

---

## Checklist da Fase 0

- [x] Passo 1 — Modelo de dados lido e entendido ✅ (30/09/2026)
- [x] Passo 2 — Estrutura de pastas criada + Git inicializado + `.gitignore`
- [x] Passo 3 — `docker-compose.yml` criado, container `healthy`, `SELECT 1` respondendo ✅ (25/09/2026)
- [x] Passo 4 — Primeira migração aplicada (11 tabelas no banco) ✅ (30/09/2026 — migration `ce7b11ad57f8`)

---

## Checklist da Fase 1 — Backend básico (autenticação e cadastro) ✅

- [x] 1.1 Config (`pydantic-settings`, `.env`) + FastAPI no ar (`GET /health`) ✅ (06/10/2026)
- [x] 1.2 Models + conector do banco (`database.py`, `get_db`) ✅ (06/10/2026)
- [x] 1.3 Schemas Pydantic (`schemas.py` — cadastro, login, token, usuário) ✅ (06/10/2026)
- [x] 1.4 Segredos: hash de senha (bcrypt) + JWT (`security.py`) ✅ (06/10/2026)
- [x] 1.5 Rota `POST /auth/cadastro` ✅ (06/10/2026)
- [x] 1.6 Rota `POST /auth/login` (valida senha, devolve token de 60 min) ✅ (06/10/2026)
- [x] 1.7 Guarda de porta (`deps.py`) + `GET /auth/me` protegida ✅ (06/10/2026)
- [x] Commit Fase 1 ✅ (06/10/2026 — `e1ddb84`)

**Testado no Swagger do zero:** cadastro 201 → login 200 + token → `/auth/me` 401 sem token e 200 com token.

---

## Checklist da Fase 2 — Perfil do atleta ✅ CONCLUÍDA (14/10/2026)

- [x] 2.1 Schemas `PerfilAtletaDados` / `PerfilAtletaSaida` (`schemas.py`) ✅ (08/10/2026)
- [x] 2.2 `PUT /perfil/completar` — criar OU atualizar ficha, idempotente, identidade vinda do token ✅ (12/10/2026)
- [x] 2.3 `GET /perfil/{id}` — perfil PÚBLICO (sem token), 404 e 422 validados ✅ (12/10/2026)
- [x] 2.4 Upload de vídeo ✅ (13/10/2026)
  - [x] 2.4A `POST /videos/upload` (multipart, extensão, 100 MB, uuid, blocos de 1 MB) + `python-multipart` instalado
  - [x] 2.4B `GET /perfil/{id}/videos` (lista pública) + `StaticFiles` em `/media`
  - [x] Bônus 2.4 — rota `/` → redirect 307 para `/docs` ✅ (13/10/2026)
- [x] 2.5 Estatísticas do atleta ✅ (14/10/2026)
  - [x] Parte A — `POST /estatisticas` + schemas `EstatisticaDados`/`EstatisticaSaida`
  - [x] Regra escolhida: **upsert (A — atualizar)** — mesma métrica/competição/temporada = atualiza valor, não duplica
  - [x] Parte B — `GET /perfil/{id}/estatisticas` público com filtros `?competicao=` e `?temporada=`
- [x] 2.6 Commit da Fase 2 ✅ — `31c3395` "Fase 2: perfil do atleta, videos e estatisticas com upsert" (8 arquivos, 522 linhas; `perfi.py` já não existia; `.docx` no `.gitignore` para ficar só na máquina)

**Testado (14/10/2026):** POST 201 com upsert (id 3 atualizado, não duplicou); lista pública 200; filtro temporada 2026 → 3 linhas; `?temporada=1999` → `[]`; `/perfil/999/estatisticas` → 404; `valor: 0` → 422; sem token → 401. ⚠️ Lição: upsert compara texto byte a byte — "Ribeirão" ≠ "Ribeirao" nasceu linha duplicada (limpa; em produção: normalizar texto na entrada).

**Testado (13/10/2026):** upload `.mp4` → 201 com uuid no disco (`media/uploads/`) e linha em `video_atleta`; `.txt` → 400; sem token → 401; arquivo servido em `/media/uploads/...` → 200 `video/mp4`; lista `/perfil/1/videos` → 200 com 2 vídeos; `/perfil/999/videos` → 404.

**Testado no Swagger (12/10/2026):** banco zerado com `TRUNCATE ... CASCADE` → cadastro 201 → login 200 → `PUT /perfil/completar` 200 (mesmo `id` na 1ª e 2ª chamada = atualizou, não duplicou) → `GET /perfil/1` 200 sem token → `/perfil/999` 404 → `/perfil/abc` 422.

---

## Checklist da Fase 3 — Busca e descoberta (FECHADA ✅ em 19/10/2026)

- [x] 3.0 Campo `nome` ✅ (concluída 16/10/2026)
  - [x] `nome` no model `Usuario` (`models.py`) — `Mapped[str | None]`, index
  - [x] `nome` em `UsuarioCadastro` (obrigatório, 2–100) e `UsuarioSaida` (`str | None`) no `schemas.py`
  - [x] `auth.py`: `nome = dados.nome` no `Usuario(...)`
  - [x] Migration 1ª: `9ed6706244c1` "fase3_nome_usuario" aplicada (`upgrade head`)
  - [x] Erro 409 (e-mail repetido) e TypeError 'nome' invalid keyword — resolvidos (didática)
  - [x] Cadastro testado → **201** com `"nome"` na resposta
  - [x] ⚠️ 2ª migration executada (16/10): `ecf66b6ee6f0` removeu `atleta.nome` + `ix_atleta_nome` (autogenerate: `Detected removed column 'atleta.nome'`)
- [x] 3.1 `GET /atletas` ✅ (16/10/2026) — vitrine pública sem token; schema `AtletaBuscaSaida` + router `routers/atletas.py` com JOIN Atleta×Usuario e `calcular_idade()`; corrigido typo `list['AtletaBuscaSaida']` → `list[AtletaBuscaSaida]` (aspas quebravam o /openapi.json)
- [x] 3.2 Filtros + paginação ✅ (16/10/2026) — `?esporte=&posicao=&estado=&categoria=` (opcionais, ilike/normalização) + `?pagina=&por_pagina=` com envelope `BuscaAtletasSaida` (total, total_paginas, resultados); corrigidos: typo `BuscaAtletaSaida`→`BuscaAtletasSaida` e função duplicada (FastAPI fica com a 1ª rota)
- [x] 3.3 Favoritar/desfavoritar (olheiro) ✅ (19/10/2026) — `PUT /olheiro/completar` (upsert) + `POST`/`DELETE /atletas/{id}/favoritar` (409 duplicado, 403 sem perfil) + `GET /meus-favoritos` (JOIN 3 tabelas, reusa AtletaBuscaSaida); roteador `routers/olheiro.py` + helper `obter_olheiro_logado`; testado fim a fim (201/409/200/[]/403)

✅ **Fase 3 encerrada** (commits `ae3e7db`).

---

## Checklist da Fase 4 — Mensagem/chat (FECHADA ✅ em 20/10/2026)

- [x] 4.1 Enviar + conversa ✅ (20/10/2026)
  - [x] Schemas `MensagemEnvia` / `MensagemSaida` (com `remetente_nome` via dicionário — 1 query, não N)
  - [x] Roteador `routers/mensagens.py` — `POST /mensagens` (404 destinatário inexistente, 422 mensagem vazia)
  - [x] `GET /mensagens/conversa/{outro_id}` — cronológico, só as que eu participei (olheiro vê só a própria conversa)
  - [x] Registro em `main.py`; fix typos do aluno (destrinatario, statu_code, contudo...) + `list[X]` vs `[X]`
  - [x] Testado 5/5: envio 201, conversa 200 com as 2 mensagens, olheiro estranho vê `[]`, destinatário 999 → 404
- [x] 4.2 Lido / não-lido ✅ (20/10/2026)
  - [x] `PUT /mensagens/lidas/{outro_id}` — `.update()` em massa (1 SQL), só as RECEBIDAS e não-lidas; schema `LidasSaida`
  - [x] `GET /mensagens/nao-lidas` — `.count()` (banco devolve só o número)
  - [x] Testado: 1 não-lida → PUT → 0; destinatário decide (remetente nunca marca)
  - [x] "Altere nos scripts pra mim" → assistente aplicou blocos em schemas.py + mensagens.py
- [x] 4.3 LGPD ✅ (20/10/2026)
  - [x] Regra: olheiro → atleta MENOR exige responsável legal com vínculo ativo; sem → **403**
  - [x] Com vínculo: `consentimento_responsavel_id` gravado na mensagem (o "recibo"); schema expõe o campo
  - [x] Reuso de `calcular_idade` (importado do router de atletas)
  - [x] Testado 4/4: 403 sem vínculo; criação do vínculo (responsável Maria id 6 + vínculo atleta 1); 201 com recibo; atleta menor → olheiro liberado (só trava olheiro→menor)
- [x] Commits da Fase 4 — `bd2cc01` (4.1+4.2) e `22514b3` (4.3 LGPD)

✅ **Fase 4 encerrada** (20/10/2026). Banco dev: mensagens id 5 (Messi→joão, com recibo) e 6 (joão→Messi); responsável Maria (id 6) vinculada ao atleta 1.

---

## Checklist da Fase 5 — Responsável Legal API (FECHADA ✅ em 21/10/2026)

- [x] Schemas `ResponsavelDados` (entrada: atleta_id + parentesco) / `ResponsavelSaida` ✅
  - [x] Fix: `ResponsavelSaida` aninhada dentro de `ResponsavelDados` (indentação) + typo `from_atributes` → `from_attributes`
- [x] Roteador `routers/responsaveis.py` — `POST /responsaveis` (404 atleta inexistente, 409 duplicado) + `GET /meus-vinculos` + `DELETE /responsaveis/{id}` ✅
  - [x] Guarda `obter_responsavel_logado` (403 se não for tipo responsavel)
  - [x] Soft delete: `vinculo_ativo = false` (histórico fica pra auditoria); só o dono do vínculo desvincula (403)
  - [x] Fix do aluno: bloco colado 2x, corpo da função sem indentação, `.first()` → `first()`
- [x] Registro em `main.py`
- [x] Testado 7/7 (21/10/2026): atleta→403; duplicado→409; meus-vinculos→200; delete→soft; Messi sem vínculo→403 LGPD; re-vincular→201; Messi com vínculo→201 + consentimento
- [x] Commit `2ee4551` — "Fase 5: API de responsavel legal (criar vinculo, meus-vinculos, soft delete)"

✅ **Fase 5 encerrada** (21/10/2026). Banco dev: vínculo id 1 (desativado, auditoria) + id 2 (ativo, mãe Maria × atleta 1); mensagem id 7 (Messi→joão com recibo 2).

---

## Checklist da Fase 6 — Avaliação bidirecional (FECHADA ✅ em 22/10/2026)

- [x] Modelo `Avaliacao` polimórfico: `avaliado_tipo` ('atleta'|'olheiro') + `avaliado_id` (substitui `atleta_id`; UniqueConstraint no par avaliador×avaliado) ✅
  - [x] Fix do aluno: Bloco 1 do models não colado + 4 typos nos schemas (`avaliacao_id`, `comentarios`, campo `avaliacao` duplicado, `avaliacao_tipo`)
- [x] Migration `7a282b4eb5c0` — drop `atleta_id`, add `avaliado_tipo`/`avaliado_id`, unique + índices ✅
- [x] Schemas `AvaliacaoDados` (nota 0–10) / `AvaliacaoSaida` / `AvaliacaoResumo` ✅
- [x] Roteador `routers/avaliacoes.py` — `POST /avaliacoes` (direção pelo tipo de quem loga; upsert 1 por par) + `GET /{tipo}/{id}` (média+comentários) + `GET /minhas` ✅
  - [x] Olheiro sem ficha pode DAR nota (404 só se avaliado inexistente); atleta só avalia olheiros (direção automática)
- [x] Registro em `main.py`
- [x] Testado 8/8 + bônus (22/10/2026): ozzy sem ficha→200; olheiro 99→404; upsert mudou 9→7 na mesma id; resumo atleta média 8.8; resumo olheiro 7.0; `/minhas` ok
- [x] Commit `f6f2192` — "Fase 6: avaliacao bidirecional olheiro x atleta com upsert e resumo"

✅ **Fase 6 encerrada** (22/10/2026). Banco dev: avaliações id 1 (ozzy→atleta1, 9.0), 2 (joão→olheiro1, 7.0 upsertada), 3 (messi→atleta1, 8.5).

---

## Checklist da Fase 7 — Dashboard de rankings (FECHADA ✅ em 22/10/2026)

- [x] Schemas `TopAtletaSaida` / `TopOlheiroSaida` / `ResumoDashboardSaida` ✅
- [x] Roteador `routers/dashboard.py` — `GET /dashboard/top-atletas`, `GET /dashboard/ranking-olheiros` (GROUP BY + AVG + HAVING + ORDER BY + LIMIT; posição de ranking feita no Python) + `GET /dashboard/resumo` ✅
- [x] `?limite` com `Query(10, ge=1, le=50)` → 422 automático fora da faixa ✅
- [x] Registro em `main.py` ✅
- [x] Testado 5/5 (22/10/2026): resumo = 6 usuários/3 avaliações/média 8.17; top-atletas = atleta 1 (zagueiro) 1º 8.75 c/ 2 avaliações; ranking-olheiros = Messi 7.0; limite=999 → 422; limite=1 → só o 1º
- [x] Fixes: 4 typos do aluno (`Video`→`VideoAtleta`, `avaliacao_tipo`→`avaliado_tipo`, `total_avaliacao(s)`, `ranking_posico(ão)`) + **bug de cross join do assistente** no resumo (6×2×5 = "60 usuários") → corrigido com contagem por tabela sem JOIN
- [x] Commit `3f8ae44` — "Fase 7: dashboard de rankings (top atletas, ranking olheiros, resumo)"

✅ **Fase 7 encerrada** (22/10/2026). Lição da fase: produto cartesiano (tabela no SELECT sem JOIN) e HAVING ≠ WHERE.

---

## Checklist da Fase 8 — Visualização de perfil (FECHADA ✅ em 27/10/2026)

- [x] `get_current_user_optional` em `deps.py` — dependência opcional (sem token = None, token ruim = 401) ✅
- [x] `GET /perfil/{id}` registra visita (anti-inflação: dono não conta; try/rollback no tracking) ✅
- [x] `GET /perfil/{id}/visualizacoes` — total, únicos, anônimas, última + últimos 10 visitantes (outerjoin) — só o dono (401/403/404) ✅
- [x] Schemas `VisitanteRecente` / `VisualizacoesSaida` ✅
- [x] Testado 8/8 (27/10/2026): anônima 200, messi 200, dono não conta (total=2), 401, 403, métricas `total=2 unicos=1 anonimas=1`, 404 id 999, OpenAPI **29 endpoints** (plano disse 31 — errado)
- [x] Fix: bloco `'''` duplicado no perfil.py (edit do assistente) → SyntaxError corrigido
- [x] Commit `21314c4` — "Fase 8: visualizacao de perfil com metricas so do dono"

✅ **Fase 8 encerrada** (27/10/2026). Lição da fase: dependência opcional, efeito colateral em GET, outerjoin vs inner join, ordem das checagens 404→403→401.

---

## Checklist da Fase 9 — Frontend React (FECHADA ✅ em 29/10/2026)

### Blocos concluídos

- [x] **9.1 Setup** ✅ (29/10/2026) — Vite 8 + React 19 + ESLint em `frontend/`; `vite.config.js` com **proxy `/api` → :8000** (evita CORS); estrutura `src/{api,components,pages}`; `src/api/client.js` (helper `api()` com params/token/erros); App.jsx "oi" renderizando em `:5173`
- [x] **9.2 Vitrine de atletas** ✅ (29/10/2026) — `react-router-dom`; tema CSS com variáveis (`index.css`); componente `CartaoAtleta` (Link SPA, avatar com inicial, `nome ?? 'Atleta'`); `pages/Vitrine.jsx` com filtros reativos (`useEffect` refaz a busca), paginação e 3 estados (loading/erro/dados); grade `auto-fill`
- [x] **9.3 Perfil do atleta** ✅ (29/10/2026) — rota `/perfil/:atleta_id` + `useParams()`; `Promise.all` (ficha + vídeos + estatísticas); `reduce` agrupando stats por competição+temporada; `Number(valor)` convertendo Decimal do JSON; player `<video src={/api+url_ou_caminho}>`; 404 do backend vira mensagem na tela
- [x] **9.4 Rankings** ✅ (29/10/2026) — página `/rankings` com 7 cards de resumo, top atletas e top olheiros; medalhas 🥇🥈🥉; `toFixed(2)` para médias; Link do top leva pro perfil
- [x] **9.5 Login + cadastro** ✅ (29/10/2026) — `AuthContext` (contexto React com token em `localStorage`); páginas Login e Cadastro; `client.js` busca token automático do `localStorage`; 401 limpa sessão; botão Sair; `Navigate` redireciona sem login
- [x] **9.6 Minha conta** ✅ (29/10/2026) — rota `/minha-conta` protegida; `EuSaida` no backend (`/auth/me` devolve `atleta_id`); form ficha (pré-preenchido via `PUT /perfil/completar`); painel visualizações; upload de vídeo (`FormData` + `client.js`); limpeza de duplicata Fase 8 no `schemas.py`
- [x] Testado 6/6 blocos (29/10/2026): vitrine 200, perfil com stats+2 vídeos, rankings com medalhas, login joão + recarregar sessão, cadastro olheiro, `/minha-conta` com ficha pré-preenchida + 4 views + upload
- [x] Commit: `pendente até agora`

### Lições desta fase

- **IPv6:** `localhost` ≠ `127.0.0.1` — o Vite escuta em `localhost` (às vezes `::1`); curl em `127.0.0.1` dava falso "HTTP 000"
- **"Erro inesperado" no React** quase sempre é erro 500 no backend → testar `/api/...` direto antes de culpar o front
- **Docker** parou de novo no meio (banco 500) → religar Docker Desktop + `docker start scoutbase-db`
- **`npm install` na raiz** (fora de `frontend/`) cria `package.json` lixo na raiz — scripts só existem em `frontend/`
- **Zumbis:** portas 5173/5174/5175 ocupadas por vite antigo → matar processos `node` com `*vite*` no CommandLine
- **Vídeos "fake":** os 2 arquivos de `backend/media/uploads/` têm 12 bytes com texto `video fake` (teste da Fase 2) — player não toca
- **Duplicatas de texto:** bloco `'''` no perfil.py (Fase 8) e classes de schemas duplicadas (Fase 8/9) — conferir sempre
- **Hook antes de return:** no React, `useState`/`useEffect` sempre antes de qualquer `return` condicional (regra do React)
