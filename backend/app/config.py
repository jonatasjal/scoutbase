# ==========================================================================
# 
# Cria uma classe de configuração centralizada, onde:
# - BaseSettngs - é a variante do Pydantic que lê valores de variáveis de ambiente e vez de exigir que passemos manualmente
# - database_url - campo com valor padrão (fallback) para conexão com Postgres local, se existir uma env var DATABASE_URL sobrescreve o padrão
# - model_config = {"env_file": ".env"} manda o Pydantic carregar automaticament um arquivo .env da raiz do projeto (útil para não expor senha de banco)
# - settings = Settings() -  instancia tudo uma única vez no import, o resto do app importa settins e usa settings.database_url
# 
# ==========================================================================

# Importa a classe base que adiciona leitura automática de env vars/.env
from pydantic_settings import BaseSettings

# Classe com a URL de conexão com o banco (valor padrão local)
class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://scoutbase:scoutbase@localhost:5432/scoutbase"
    # Diz ao Pydantic par ler variáveis do arquivo .env (garante as sehas fora do código)
    model_config = {"env_file": ".env"}

    # Segredo que assina os tokens JWT (obrigatório vir do .env; sem default
    # de propósito: se faltar, o app FALHA EM VEZ de usar chave fraca)
    secret_key: str
    # Algoritmo de assinatura (HS256 = " HMAC + SHA-256", padrão do PyJWT)
    algorithm: str = "HS256"
    # Quanto tempo o token vale (em minutos) - vem do .env, default 60
    access_token_expire_minutes: int = 60

    # Fase 15: DEBUG: true só NO PC LOCAL (devolver token para testar sem SMTP)
    # Na Render não existe tal variável -> default é False -> nunca faz o token
    debug: bool = False
    # config de email (SMTP): enquanto vazias, o envio roda em MODO SIMULAÇÃO
    # (imprime no console). Preencher depois = email de verdade
    smtp_host: str| None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None

# Instancia as configurações uma única vez (singleton) para importar em todo o app
settings = Settings()