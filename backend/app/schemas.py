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
from app.models import TipoUsuario, Plano

# Data/hora para o campo criado_em da resposta
from datetime import datetime


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
