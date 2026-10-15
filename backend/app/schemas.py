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



