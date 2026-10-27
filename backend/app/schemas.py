# ==========================================================================
# SCHEMAS — as "portarias" da API (modelos Pydantic)
#
# - Por que existe: o banco tem tabelas (models.py), mas quem CHEGA pela
#   internet manda texto (JSON). O schema é a régua que valida esse JSON
#   ANTES de chegar perto do banco: campo obrigatório? e-mail com @?
#   senha com tamanho mínimo? Se não passar, o FastAPI devolve erro 422
#   automaticamente — nem chega no nosso código.
#
# - BaseModel — classe base do Pydantic: você declara os campos e o tipo,
#   ele faz a validação e ainda gera exemplos automáticos no /docs.
#
# - EmailStr — tipo "e-mail" do Pydantic: exige formato válido (tem @,
#   tem domínio...). Por isso instalamos o pacote email-validator.
#
# - Field(min_length=...) — regras extras do campo (aqui: senha mín. 6).
#
# - from_attributes = True — permite montar a resposta direto de um objeto
#   do banco (ex: Usuario(id=1, email=...)), sem converter na mão.
#
# REGRA DE OURO: schema de ENTRADA tem senha; schema de SAÍDA NUNCA tem
# senha. Aqui separamos os dois de propósito (o que entra ≠ o que sai).
# ==========================================================================

# BaseModel do Pydantic + Field para regras de tamanho + EmailStr p/ e-mail
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# Tipos de dados do app (enums vindos dos models, por isso são str, enum.Enum)
from app.models import TipoUsuario, Plano, Esporte, TipoOrigemVideo

# Data/hora para o campo criado_em da resposta
from datetime import datetime, date


# ---------------------------------------------------------------------------
# ENTRADA — o que o cliente manda para se cadastrar
# ---------------------------------------------------------------------------
class UsuarioCadastro(BaseModel):
    # Obrigatório e precisa ser e-mail válido (senão: erro 422 automático)
    email: EmailStr
    # min 6 / max 72: 6 por regra de segurança; 72 porque o bcrypt só
    # enxerga os primeiros 72 caracteres (acima disso, ignora o resto)
    senha: str = Field(min_length = 6, max_length = 72)

    # Nome completo: 2 m´´inimpos (evita "a"), 100 de máximo (igual o banco)
    nome: str = Field(min_length = 2, max_length = 100)

    # Padrao "atleta": se o cliente não informar, cria como atleta
    tipo_usuario: TipoUsuario = TipoUsuario.atleta


# ---------------------------------------------------------------------------
# ENTRADA — o que o cliente manda para fazer login (só email + senha)
# ---------------------------------------------------------------------------
class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str


# ---------------------------------------------------------------------------
# SAÍDA — resposta do login: o crachá (token) que o cliente vai usar
# ---------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str            # o JWT em si (string longa)
    token_type: str = "bearer"   # "como usar": no cabeçalho Authorization: Bearer <token>


# ---------------------------------------------------------------------------
# SAÍDA — dados públicos do usuário (SEM senha, SEM hash)
# ---------------------------------------------------------------------------
class UsuarioSaida(BaseModel):
    id: int
    nome: str | None    # Usamos  | None porque contas antigas ainda não têm
    email: EmailStr
    tipo_usuario: TipoUsuario
    plano: Plano
    criado_em: datetime
    # Liga o schema aos objects do banco (aceita instancia de Usuario)
    model_config = ConfigDict(from_attributes = True)


# ---------------------------------------------------------------------------
# ENTRADA — dados para COMPLETAR o perfil do atleta (PUT /perfil/completar)
# ---------------------------------------------------------------------------
class PerfilAtletaDados(BaseModel):
   # NASCIMNENTO, não idade - idade envelhece a data não, então é melhor guardar a data de nascimento e calcular a idade na hora
   # a idade é calculada na hora da busca a partir daqui
   data_nascimento: date
   # Opcional: se o cliente não mandar, vale "futebol" como detault do enum
   esporte: Esporte = Esporte.futebol
   # Obrigatórios = exatamente os campos que a tabela "atleta" exige
   # Os limites (50,30,100) são IGUAIS aos String(...) do banco]
   # assim o erro aparece como 422 na API, antes de estourar o banco
   posicao: str = Field(max_length = 50)                # zagueiro, meia,...
   categoria: str = Field(max_length = 30)              # sub-15, sub-17, profissional,...
   cidade: str = Field(max_length = 100)                # cidade do atleta
   estado: str = Field(min_length = 2, max_length = 2)  # sigla do estado (UF)
   # Opcionais: aceitam None (as colunas no banco permitem NULL)
   clube_atual: str | None = Field(default = None, max_length = 100)  # clube atual do atleta
   bio: str | None = None


# ---------------------------------------------------------------------------
# SAÍDA — o perfil completo (é o que o GET público vai devolver)
# ---------------------------------------------------------------------------
class PerfilAtletaSaida(BaseModel):
    id: int
    usuario_id: int
    data_nascimento: date
    esporte: Esporte
    posicao: str
    categoria: str
    cidade: str
    estado: str
    clube_atual: str | None
    bio: str | None
    # Mesmo truque do UsuarioSaida: monta a resposta direto
    # do objeto do banco sem converter campo por campo
    model_config = ConfigDict(from_attributes = True)


'''
Acima temos 2 schemas separados (entrada e saída) pois o de ENTRADA tem só o que o usuário preenche
Já a SAÍDA mostra o que o banco guardou (com id, usuario_id). Isso é uma Rega da FASE 1, onde o que sai nunca tem senha/senha_hash
'''

# ---------------------------------------------------------------------------
# SAÍDA — o que devolvemos quando alguém pede um vídeo
# ---------------------------------------------------------------------------
# Repare: não existe schema de ENTRADA para vídeo, porque o vídeo NÃO chega
# em JSON — chega como arquivo (multipart). O Pydantic só entra na saída
class VideoSaida(BaseModel):
    id: int
    atleta_id: int
    tipo_origem: TipoOrigemVideo        # 'arquivo_upload' ou 'link_externo'
    url_ou_caminho: str                 # onde o arquivo é guardado
    titulo: str
    tamanho_bytes: int | None = None    # | None = pode ser nulo (link não tem)
    data_upload: datetime

    model_config = ConfigDict(from_attributes = True)


# ---------------------------------------------------------------------------
# ESTATÍSTICAS — métricas genéricas do atleta (gols, jogos, aces...)
# ---------------------------------------------------------------------------
# Decimal em vez de float: "3.00" e "3" são o MESMO número exato.
# float tem erro de arredondamento de computador (0.1 + 0.2 != 0.3 em
# float!); Decimal não — por isso o banco também usa Numeric(10,2).
from decimal import Decimal

# Entrada - o atleta registra UMA métrica (sem id e sem atleta_id)
# o dono vem do token e o banco é que gera o id
class EstatisticaDados(BaseModel):
    competicao: str = Field(..., max_length = 100, examples = ['Copa Ribeirão Preto'])
    temporada: str = Field(..., max_length = 10, examples = ['2026'])
    metrica: str = Field(..., max_length = 50, examples = ['gols', 'assistências', 'jogos'])
    valor: Decimal = Field(..., gt = 0, examples = [3])  # gt = "greater than" = maior que zero (métrica 0 não vale registrar)

# Saída - o que devolvemos (inclui o id que o banco criou)
class EstatisticaSaida(BaseModel):
    id: int
    atleta_id: int
    competicao: str
    temporada: str
    metrica: str
    valor: Decimal

    model_config = ConfigDict(from_attributes = True)


# ---------------------------------------------------------------------------
# SAÍDA da vitrine — cartão público do atleta (busca sem login)
# ---------------------------------------------------------------------------
class AtletaBuscaSaida(BaseModel):
    # id do Perfil de atleta  (NÃO é o da conta)
    id: int
    # o nome vem de Usuario (pode ser None em contas anigas -> vitrine mstra "Atleta")
    nome: str | None
    esporte: Esporte
    posicao: str
    categoria: str
    cidade: str
    estado: str
    clube_atual:str | None
    idade: int
    # Idade calculada a partir de data_nascimento, ou seja, nunca será guardada e com isso ela nunca "envelhece" no banco
    # a data cheia não é exposta seguindo padrões de privacidade

'''
Por que um schema novo em vez de reusar PerfilAtletaSaida? Porque o perfil (GET /perfil/{id}) é 
"meu perfil completo"; a vitrine é um cartão resumido para olheiro ver de longe. 
Expor tudo publicamente seria falta de privacidade — o Pydantic aqui é a portaria que decide o que o público vê.
'''

# ---------------------------------------------------------------------------
# SAÍDA da busca — o "envelope" da paginação
# ---------------------------------------------------------------------------
class BuscaAtletasSaida(BaseModel):
    # total = quantos atletas casaram os filtros (não o total do banco todo)
    total: int                          
    pagina: int             # qual página o cliente pediu
    por_pagina: int         # quantos por página ele quer
    total_paginas: int      # para o front desenhar "página 2 de 7"
    resultados: list[AtletaBuscaSaida]  # lista de atletas dessa página


# ---------------------------------------------------------------------------
# ENTRADA — dados para completar a ficha do OLHEIRO (PUT /olheiro/completar)
# ---------------------------------------------------------------------------
class OlheiroCompleta(BaseModel):
    # Tudo OPCIONAL de propóstivo: o olheiro pode preencher só o que quiser agora e o resto depois
    # Os limites = menos String(...) do banco
    organizacao: str | None = Field(default = None, max_length = 100)
    cargo: str | None = Field(default = None, max_length= 50)


# ---------------------------------------------------------------------------
# SAÍDA — a ficha do olheiro (como o GET /perfil/{id} faz pro atleta)
# ---------------------------------------------------------------------------
class OlheiroSaida(BaseModel):
    id: int
    usuario_id: int
    organizacao: str | None
    cargo: str | None
    verificado: bool       # selo de "verificado" para olheiros (atualmente False)
    model_config = ConfigDict(from_attributes = True)   # deixa o Pydantic aceitar o objeto do banco direto (sem converter na mão)


# ---------------------------------------------------------------------------
# SAÍDA — um favorito gravado (POST / DELETE /atletas/{id}/favoritar)
# ---------------------------------------------------------------------------
class FavoritoSaida(BaseModel):
    olheiro_id: int
    atleta_id: int
    criado_em: datetime
    model_config = ConfigDict(from_attributes = True)


# ---------------------------------------------------------------------------
# FASE 4 — MENSAGENS
# ---------------------------------------------------------------------------

# ENTRADA — o que a pessoa manda pra enviar mensagem
class MensagemEnvia(BaseModel):
    destinatario_id: int = Field(gt=0)  # gt = "greater than" → só aceita número > 0
    conteudo: str = Field(min_length=1, max_length=2000)
    #   min_length=1: não deixa enviar mensagem VAZIA (só espaços ainda passa —
    #   a gente vira o str.strip() no router pra resolver)

# SAÍDA — uma mensagem como ela sai pro front
#   O que muda vs. entrada: ganha id, data/hora, e o NOME de quem mandou
#   (aí o front não precisa fazer outra requisição pra mostrar "Messi: oi")
class MensagemSaida(BaseModel):
    id: int
    remetente_id: int
    destinatario_id: int
    remetente_nome: str | None   # nome de quem enviou (pode ser NULL no banco → aceitamos None)
    conteudo: str
    lida: bool
    consentimento_responsavel_id: int | None
    #   Fase 4.3 (LGPD): se o remetente é olheiro e o destinatário é MENOR,
    #   guardamos aqui o id do responsável que autorizou (o "recibo").
    #   None = normal (adulto, não-atleta, ou atleta mandando).
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# FASE 4.2 — LIDO / NÃO LIDO
# ---------------------------------------------------------------------------

# SAÍDA — resultado de "marcar como lido" (resumo do que mudou)
class LidasSaida(BaseModel):
    mensagens_marcadas: int   # quantas mensagens passaram de false → true
    

# ---------------------------------------------------------------------------
# FASE 5 — RESPONSÁVEL LEGAL (API do vínculo LGPD)
# ---------------------------------------------------------------------------
# Entrada -> criar vínculo responsável x atleta
class ResponsavelDados(BaseModel):
    atleta_id: int = Field(gt=0)
    # gt = greater than (maior que) - id 0 ou negativo não existe
    parentesco: str = Field(min_length = 2, max_length = 30)
    # 'mãe', 'pai', 'tutor' ...mesmo limite do banco (String(30))

# Saída - resumo do vínculo
class ResponsavelSaida(BaseModel):
    id: int
    atleta_id: int
    parentesco: str
    vinculo_ativo: bool
    criado_em: datetime
    model_config = ConfigDict(from_attributes = True)

# ---------------------------------------------------------------------------
# FASE 6 — AVALIAÇÃO (olheiro × atleta, bidirecional)
# ---------------------------------------------------------------------------
class AvaliacaoDados(BaseModel):
    avaliado_id: int = Field(gt=0)
    nota: float = Field(ge=0, le=10)        # de 0 a 10, o resto o pydantic barra
    comentario: str | None = Field(default = None, max_length = 500)

class AvaliacaoSaida(BaseModel):
    id: int
    avaliador_id: int
    avaliado_tipo: str
    avaliado_id: int
    nota: float
    comentario: str | None
    criado_em: datetime
    model_config = ConfigDict(from_attributes = True)

class AvaliacaoResumo(BaseModel):
    avaliado_tipo: str
    avaliado_id: int
    total_avaliacoes: int
    media_nota: float | None        # None = ninguém avaliou ainda
    comentarios: list[str]          # os textos, mais recentes primeiro

# ========================================================
# FASE 7 — DASHBOARD (rankings e números da plataforma)
# ========================================================
class TopAtletaSaida(BaseModel):
    # Uma linha do ranking de atletas
    atleta_id: int
    nome: str | None
    posicao: str | None = None
    media_nota: float           # AVG(nota)
    total_avaliacoes: int       # COUNT(*)
    ranking_posicao: int        # 1º, 2º, 3º... (a ordem é a posição na lista)

class TopOlheiroSaida(BaseModel):
    # Uma linha do ranking de olheiros (reputação de quem olha)
    olheiro_id: int
    nome: str | None
    organizacao: str | None = None
    media_nota: float
    total_avaliacoes: int
    ranking_posicao: int

class ResumoDashboardSaida(BaseModel):
    # Os nºs gerais do topo do painel
    total_usuarios: int
    total_atletas: int
    total_olheiros: int
    total_avaliacoes: int
    media_geral_nota: float     # média de TODAS as notas sem agrupar
    total_videos: int
    total_mensagens: int

'''
- ranking_posicao — o Python (não o SQL) escreve o número do lugar: a 1ª linha da lista = posição 1
- media_nota: float — o banco guarda nota como Decimal (exato); o Pydantic converte pra float na saída (ok aqui, é só exibição)
- ResumoDashboardSaida — a "capa" do painel: contagens totais em uma query só
'''

# ========================================================
# FASE 8 — VISUALIZAÇÕES DO PERFIL
# ========================================================
class VisitanteRecente(BaseModel):
    # 1 visita na lista "quem andou por aqui"
    usuario_id: int | None     # None = anônimo (visitou sem login)
    nome: str | None           # nome de quem logou (None se anônimo)
    visto_em: datetime         # quando a visita aconteceu

class VisualizacoesSaida(BaseModel):
    # O painel "meu perfil foi visto" — só o dono recebe
    atleta_id: int
    total_visitas: int         # COUNT(*) de linhas da tabela
    visitantes_unicos: int     # DISTINCT de quem LOGOU (anônimos ficam de fora)
    visitas_anonimas: int      # WHERE visitante IS NULL
    ultima_visita: datetime | None   # MAX(criado_em) — None se nunca viram
    visitantes_recentes: list[VisitanteRecente]   # últimos 10

'''
- total vs únicos: 5 visitas do MESMO olheiro = 5 totais, 1 único.
  "Total" mede frequência; "únicos" mede ALCANCE.
- anônimas: entram no total, mas NÃO em visitantes_unicos
  (sem login não dá pra saber quem foi -> não vira "visitante")
'''

# ========================================================
# FASE 8 — VISUALIZAÇÕES DO PERFIL
# ========================================================
class VisitanteRecente(BaseModel):
    # 1 visita na lista "quem andou por aqui"
    usuario_id: int | None     # None = anônimo (visitou sem login)
    nome: str | None           # nome de quem logou (None se anonimo)
    visto_em: datetime         # quando a visita ocorreu

class VisualizacoesSaida(BaseModel):
    # O painel "meu perfil foi visto" — só o dono recebe
    atleta_id: int
    total_visitas: int                  # COUNT(*) de linhas da tabela
    visitantes_unicos: int              # DISTINCT de quem LOGOU (anônimos ficam de fora)
    visitas_anonimas: int               # WHERE visitante IS NULL
    ultima_visita: datetime | None      # MAX(criado_em) — None se nunca viram
    visitantes_recentes: list[VisitanteRecente]   # últimos 10

'''
- total vs únicos: 5 visitas do MESMO olheiro = 5 totais, 1 único.
  "Total" mede frequência; "únicos" mede ALCANCE.
- anônimas: entram no total, mas NÃO em visitantes_unicos
  (sem login não dá pra saber quem foi -> não vira "visitante")
- datetime já importado no topo do arquivo (linha 32)
'''