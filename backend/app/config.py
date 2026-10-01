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

# Instancia as configurações uma única vez (singleton) para importar em todo o app
settings = Settings()