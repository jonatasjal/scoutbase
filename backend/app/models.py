# ---------------------------------------------------------------------------
# IMPORTS — o que cada biblioteca traz
# ---------------------------------------------------------------------------
# enum         → cria "menus fechados" (valores permitidos), ex: tipo de usuário
# datetime     → tipos de data/hora (para colunas de data e hora)
# decimal      → número decimal EXATO (dinheiro/notas; diferente de float, que arredonda)
#
# Do SQLAlchemy (biblioteca que transforma Python em SQL):
#   Boolean, Date, DateTime, String, Text, Numeric, BigInteger
#                          → os TIPOS de coluna (texto, número, data...)
#   Enum                   → coluna que aceita só valores de um menu fechado
#   ForeignKey             → "chave estrangeira": liga esta linha a outra tabela
#                            (ex: atleta.usuario_id aponta para usuario.id)
#   Index                  → índice: atalho de leitura que deixa a busca RÁPIDA
#   UniqueConstraint       → regra "essa combinação de colunas não pode repetir"
#   func.now()             → função do BANCO que marca a hora atual (não a do PC)
#
#   Mapped[...]            → diz o TIPO de cada coluna (para Python/IDE)
#   mapped_column(...)     → diz as REGRAS da coluna (tamanho, índice, padrão)
#   Base                   → classe-mãe vinda do nosso database.py; toda model
#                            herda dela → é ela que o Alembic lê para saber as tabelas

import enum
from datetime import datetime, date
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

# ========================================================
# ENUMS - menu fechado de valores permitidos
# ========================================================
# Por que existe: sem enum, alguém poderia gravar tipo_usuario = "jogador de sinuca"
# e o sistema quebraria silenciosamente. O enum vira um CREATE TYPE no Postgres:
# o PRÓPRIO banco recusa o valor inválido na entrada

class TipoUsuario(str, enum.Enum):
    # Quem é o dono da conta? (o "perfil" do usuário)
    atleta = "atleta"
    olheiro = "olheiro"
    responsavel = "responsavel"
    patrocinador = "patrocinador"     # ainda não implementado mas para futuramente

class Plano(str, enum.Enum):
    # Fremium: hoje ningu´m paga, mas o CAMPO jpa existe quando mudar para modo de cobrança
    gratuito = "gratuito"
    pago = "pago"

class Esporte(str, enum.Enum):
    # Só futebol na V1, mas o enum já permite acrescentar "volei" sem mudar schema
    futebol = "futebol"               # único habilitado para essa versão

class TipoOrigemVideo(str, enum.Enum):
    # Vídeo veio de um link (Youtube) ou de arquivos enviados pelo usuário?
    link_externo = "link_externo"
    arquivo_upload = "arquivo_upload"


# ---------------------------------------------------------------------------
# 1. Usuario — conta de login, INDEPENDENTE do perfil
# ---------------------------------------------------------------------------
# Por que separar "Usuario" das tabelas de perfil (Atleta, Olheiro)?
# Por que login é igual para todos (email + senha), mas o que cada um TEM
# de dados é diferente. Assim: 1 conta = 1 linha em "usuario" + 1 linha
# na tabela do seu perfil específico.

class Usuario(Base):
    __tablename__ = "usuario"   # nome da tabela no banco

    id: Mapped[int] = mapped_column(primary_key = True)
    # primary_key = a CHAVE única de cad alinha

    nome: Mapped[str | None] = mapped_column(String(100), index = True)
    #   | None = OPCIONAL de propósito: quem já está cadastrado (o joao) não tem
    #   nome ainda → a migration cria a coluna vazia (NULL) e nada quebra.
    #   Nos NOVOS cadastros o nome vem obrigatório (schema do Pydantic exige).
    #   Depois, num refinamento, tornaríamos obrigatório no banco também.
    #   index = ordenar/filtrar por nome na vitrine fica rápido

    email: Mapped[str] = mapped_column(String(255), unique = True, index = True)
    # String(255) = texto até 255 caracteres
    # unique = NÃO pode repetir (1 email= 1 conta)
    # index = índice (login e busca por email são mais rápidos)

    senha_hash: Mapped[str] = mapped_column(String(255))
    # NUNCA a senha em TEXTO PURO, nós guardamos um "resumo" (hash) da senha
    # Comparar hashes funciona se o banco vazar, ninguém lê a senha real

    tipo_usuario: Mapped[TipoUsuario] = mapped_column(
        Enum(TipoUsuario, name="tipo_usuario"), default=TipoUsuario.atleta
    )
    # Enum() - cria o tipo nativo "tipo_usuario" no Postgres
    # default - se ninguém informar, vira "atleta"

    plano: Mapped[Plano] = mapped_column(Enum(Plano, name = 'plano'), default = Plano.gratuito)
    # Freemium estrutural = campo pronto, conbrança só em uma eventual implementação

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default = func.now())
    # server_default = func.now() - o banco preenche a hora sozinho (padrão ISO)
    # imune a fuso horário do PC


# ---------------------------------------------------------------------------
# 2. Atleta — dados esportivos, 1-para-1 com um Usuario do tipo "atleta"
# ---------------------------------------------------------------------------
# É a ficha esportiva da pessoa: nasceu quando, joga onde, qual posição.

class Atleta(Base):
    __tablename__ = "atleta"

    id: Mapped[int] = mapped_column(primary_key=True)

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    #   ForeignKey = "este id EXISTE na tabela usuario" (integridade referencial:
    #   o banco barra cadastro de atleta com usuario_id inexistente)
    #   unique     = 1 conta nunca vira 2 perfis de atleta (relação 1-1)

    data_nascimento: Mapped[date] = mapped_column(Date, index=True)
    #   Guardamos a NASCIMENTO, não a "idade"!
    #   Por quê: idade envelhece — quem é "15 anos" hoje tem 16 no ano que vem.
    #   A idade é CALCULADA na hora da busca a partir da data de nascimento.
    #   index → busca por faixa etária fica rápida.

    esporte: Mapped[Esporte] = mapped_column(
        Enum(Esporte, name="esporte"), default=Esporte.futebol, index=True
    )

    posicao: Mapped[str] = mapped_column(String(50), index=True)
    #   ex: "zagueiro", "meia" — index porque é filtro de busca

    categoria: Mapped[str] = mapped_column(String(30), index=True)  # sub-15, sub-17...
    cidade: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(2), index=True)
    #   2 letras (SP, RJ) + índice → filtro "região" rápido (diferencial do projeto
    #   é justamente o interior/regiões negligenciadas)

    clube_atual: Mapped[str | None] = mapped_column(String(100))
    bio: Mapped[str | None] = mapped_column(Text)
    #   O "| None" significa OPCIONAL → a coluna aceita NULL (campo vazio).
    #   Text (sem tamanho) = bio longa; String(100) = texto curtinho e limitado.


# ---------------------------------------------------------------------------
# 3. ResponsavelLegal — vínculo responsável × atleta menor de idade
# ---------------------------------------------------------------------------
# Projeto envolve MENORES de idade → LGPD exige consentimento de um responsável.
# Esta tabela É esse vínculo: sem ela, não há o que registrar como "consentimento".

class ResponsavelLegal(Base):
    __tablename__ = "responsavel_legal"
    __table_args__ = (
        # Índice composto: "me mostre os vínculos ATIVOS daquele atleta"
        # (2 colunas juntas → a consulta com as 2 condições voa)
        Index("ix_resp_legal_atleta_vinculo", "atleta_id", "vinculo_ativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    #   O responsável TAMBÉM é um Usuario (tipo "responsavel")

    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"))
    #   E está ligado a UM atleta (pode ter vários vínculos: 1 responsável,
    #   vários filhos → por isso aqui NÃO tem unique)

    parentesco: Mapped[str] = mapped_column(String(30))  # mãe, pai, tutor
    vinculo_ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    #   false = o responsável perdeu a tutela, mas o HISTÓRICO fica (auditoria)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# 4. VideoAtleta — link externo OU arquivo enviado
# ---------------------------------------------------------------------------
# É o "currículo visual" do atleta. Uma tabela cobre os 2 casos porque
# o enum TipoOrigemVideo diz qual dos dois está gravado em cada linha.

class VideoAtleta(Base):
    __tablename__ = "video_atleta"

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"), index=True)
    #   index → "listar os vídeos daquele atleta" é consulta comum

    tipo_origem: Mapped[TipoOrigemVideo] = mapped_column(
        Enum(TipoOrigemVideo, name="tipo_origem_video"),
        default=TipoOrigemVideo.link_externo,
    )
    url_ou_caminho: Mapped[str] = mapped_column(String(500))
    #   Guarda um CAMINHO/URL, não o vídeo em si! Banco de dados guarda texto,
    #   arquivo pesado fica no disco (pasta media/uploads) — ver documentação 9.4

    titulo: Mapped[str] = mapped_column(String(200))
    tamanho_bytes: Mapped[int | None] = mapped_column(BigInteger)
    #   BigInteger = número grande (bytes). Nulo se for link (não temos o arquivo).

    data_upload: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# 5. EstatisticaAtleta — GENÉRICA (métrica + valor), aguenta qualquer esporte
# ---------------------------------------------------------------------------
# Decisão de design importante: em vez de colunas fixas "gols", "assistências",
# "jogos" (que serviriam só pro futebol), guardamos N linhas do tipo:
#   competicao="Copa XYZ" | temporada="2026" | metrica="gols" | valor=3
# Assim, vôlei no futuro usa a MESMA tabela com metrica="aces".

class EstatisticaAtleta(Base):
    __tablename__ = "estatistica_atleta"
    __table_args__ = (
        # Índice composto p/ painel de estatísticas: "me traga as métricas
        # daquele atleta NAQUELE torneio daquela temporada"
        Index("ix_estat_comp", "atleta_id", "competicao", "temporada"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"))
    competicao: Mapped[str] = mapped_column(String(100))
    temporada: Mapped[str] = mapped_column(String(10))  # ex: "2026"
    metrica: Mapped[str] = mapped_column(String(50))  # gols, assistencias, jogos...
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    #   Numeric(10,2) = até 10 dígitos, 2 depois da vírgula (ex: 12.50)
    #   Decimal em vez de float: número EXATO (float tem erro de arredondamento)


# ---------------------------------------------------------------------------
# 6. Olheiro — perfil profissional ligado a um Usuario
# ---------------------------------------------------------------------------
# Mesma lógica do Atleta: dados do "trabalho" ficam separados do login.

class Olheiro(Base):
    __tablename__ = "olheiro"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), unique=True)
    #   unique = 1 conta de olheiro → 1 ficha de olheiro (1-1, igual Atleta)

    organizacao: Mapped[str | None] = mapped_column(String(100))
    cargo: Mapped[str | None] = mapped_column(String(50))
    verificado: Mapped[bool] = mapped_column(Boolean, default=False)
    #   Selo de verificação é Fase 2 — o campo já existe desde o MVP


# ---------------------------------------------------------------------------
# 7. Favorito — relação MUITOS×MUITOS Olheiro × Atleta
# ---------------------------------------------------------------------------
# Um olheiro favorita VÁRIOS atletas; um atleta pode ser favoritado por VÁRIOS
# olheiros → relação N×N. No SQL, N×N SEMPRE vira uma tabela "ponte" (aqui, Favorito).

class Favorito(Base):
    __tablename__ = "favorito"
    __table_args__ = (
        UniqueConstraint("olheiro_id", "atleta_id", name="uq_favorito_olheiro_atleta"),
        # Regra do BANCO: a MESMA combinação (olheiro, atleta) não se repete.
        # Sem isso, um bug duplicaria o mesmo favorito 1000 vezes.
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    olheiro_id: Mapped[int] = mapped_column(ForeignKey("olheiro.id"))
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# 8. Mensagem — chat olheiro ↔ atleta + log de consentimento LGPD
# ---------------------------------------------------------------------------
# Os dois lados são Usuario (remetente/destinatario) porque tanto olheiro
# quanto atleta/responsável têm conta de login.

class Mensagem(Base):
    __tablename__ = "mensagem"
    __table_args__ = (
        # Índice da "caixa de entrada": filtrar por (quem enviou, quem recebeu)
        Index("ix_mensagem_remetente_destinatario", "remetente_id", "destinatario_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    remetente_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    destinatario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    conteudo: Mapped[str] = mapped_column(Text)  # Text = mensagem longa
    lida: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    consentimento_responsavel_id: Mapped[int | None] = mapped_column(
        ForeignKey("responsavel_legal.id")
    )
    #   ⭐ Peça de LGPD: quando a conversa envolve atleta MENOR, esta coluna
    #   guarda QUAL responsável autorizou. Se for atleta maior → fica NULA
    #   (por isso o "| None"). É o "recibo" de consentimento da conversa.


# ---------------------------------------------------------------------------
# 9. Avaliacao — recomendação de um avaliador sobre um atleta (Fase 2)
# ---------------------------------------------------------------------------
# Está no modelo DESDE JÁ de propósito: criar tabela depois é migrate novo;
# já existir vazia custa zero.

class Avaliacao(Base):
    __tablename__ = "avaliacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"), index=True)
    avaliador_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    #   Quem avaliou: um usuário (ex: técnico) — ainda sem entidade "tecnico"

    nota: Mapped[Decimal] = mapped_column(Numeric(3, 1))
    #   Numeric(3,1) = ex: 8.5 (até 99.9) — nota com 1 casa decimal

    comentario: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# 10. Visualizacao — dashboard "quantas vezes meu perfil foi visto"
# ---------------------------------------------------------------------------
# Requisito funcional nº 9 do MVP. Cada visita vira 1 LINHA aqui;
# o dashboard só CONTA linhas (total, únicas, anônimas).

class Visualizacao(Base):
    __tablename__ = "visualizacao"
    __table_args__ = (
        # Índice composto: contar visitas de um atleta NUM PERÍODO
        # ("views desta semana") — a data junto do id acelera esse filtro
        Index("ix_visualizacao_atleta_criado", "atleta_id", "criado_em"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey("atleta.id"))
    usuario_visitante_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    #   NULO = visita de quem NÃO tinha login (anônima) → mesmo assim conta view
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


