# ==========================================================================
# - bcrypt — é a biblioteca que transforma a senha do usuário em um código
#   irreversível. Nunca guardamos a senha "de verdade" no banco; guardamos
#   esse código (chamado "hash"). Assim, se vazarem o banco, ninguém acha
#   a senha original.
#
# - gensalt() — o "sal" (salt): um sufixo aleatório embaralhado em cada
#   hash. Por quê? Sem ele, duas pessoas com a senha "123456" teriam o
#   MESMO código no banco (dá pra cruzar dados). Com sal aleatório, cada
#   hash fica único, mesmo para senhas iguais.
#
# - hashpw(senha, salt)  ->  senha vira código   (não dá pra voltar)
# - checkpw(senha, hash) ->  True/False          (confere se é a mesma)
#
# - encode('utf-8') — o bcrypt trabalha com bytes (sequências de números),
#   não com texto; o Python usa texto (str), então traduzimos nos 2 sentidos.
#
# ATENÇÃO: não existe "des-hash". Se o usuário esquecer a senha, o caminho
# é redefinir (nova senha), nunca recuperar a antiga.
# ==========================================================================

# Importa a biblioteca de hash de senhas
import bcrypt

# --- JWT (crachá digital) ---
# datetime/timedelta: para calcular QUANDO o token expira
from datetime import datetime, timedelta, timezone
# jwt: biblioteca PyJWT - monta e confere o token
import jwt
# settings: traz a SECRET_KEY e a validade do arquivo .env
from app.config import settings


# Senha em texto -> código irreversível (guardar no banco)
def hash_senha(senha: str) -> str:
    # bcrypt.hashpw: transforma a senha em hash; bcrypt.gensalt(): gera o sal aleatório
    # O resultado sai em bytes, por isso .decode('utf-8') volta para texto
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Confere se a senha digitada corresponde ao hash guardado (True/False)
def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        # checkpw tenta "fechar a chave": se bater com o hash, True
        return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))
    except ValueError:
        # Hash corrompido/vazio no banco -> trata como senha incorreta
        return False


# ==========================================================================
# JWT — o crachá emitido no login
#
# Como ele é feito (3 partes coladas com ponto, tipo "aaa.bbb.ccc"):
#   1. header  -> diz "é um JWT e usa o algoritmo HS256"
#   2. payload -> os DADOS: quem é (id), que tipo, quando expira
#   3. assinatura -> HMAC-SHA256 do payload FEITA COM A SECRET_KEY
#
# Por que é seguro: o payload é legível por qualquer um (não é criptografia!),
# mas ALTERAR qualquer letra quebra a assinatura — e só o servidor tem a
# chave pra re-assinar. Então dá pra ler, mas NÃO dá pra forjar.
#
# exp = obrigatório: sem prazo de validade, um token roubado serviria pra
# sempre. Aqui vale 60 minutos (configurável no .env).
# ==========================================================================
def criar_token(id_usuario: int, tipo_usuario: str) -> str:
    # Hora de agora em UTC + validade (datetime do PyJWT vira timestamp no token)
    expira_em = datetime.now(timezone.utc) + timedelta(minutes = settings.access_token_expire_minutes)

    # Conteúdo do crachá (payload)
    payload = {
        'sub': str(id_usuario),      # "subject" = quem é o dono (string, por convenção JWT)
        'tipo': tipo_usuario,        # atleta / olheiro (evita ir no banco a cada request)
        'iat': datetime.now(timezone.utc),  # emitido em (issued at)
        'exp': expira_em             # expira em (expiration)
    }

    # Monta e assina: payload + segredo + algoritmo -> "header.payload.assinatura"
    return jwt.encode(payload, settings.secret_key, algorithm = settings.algorithm)


# Confere um token vindo do cliente (True se válido; False se forjado/expirado)
def verificar_token(token: str) -> dict | None:
    try:
        # decode RECALCULA a assinatura com a SECRET_KEY; se bater, devolve o payload
        return jwt.decode(token, settings.secret_key, algorithms = [settings.algorithm])
    except jwt.ExpiredSignatureError:
        # Assinatura ok mas o "exp" já passou
        return None
    except jwt.InvalidTokenError:
        # Assinatura quebrada, token aleatório ou formato errado
        return None
