# ==========================================================================
# CONFTEST.PY — a "cozinha" dos testes (o pytest lê este arquivo SOZINHO,
# sem ninguém importar). Aqui montamos o cenario de todos os testes:
# cliente HTTP fake + banco descartavel (SQLite em memoria).
# SEM rede, SEM Docker, SEM tocar no banco real.
# ==========================================================================
# pytest = framework que acha funcoes test_*, roda cada uma e confere os assert
import pytest
# TestClient = cliente HTTP que fala com o nosso app direto na memoria (sem porta)
from fastapi.testclient import TestClient
# create_engine/sessionmaker = mesmos tipos do app, so que apontando pro SQLite de teste
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# StaticPool = "todas as conexoes apontam pro MESMO banco em memoria"
# (sem ele, cada conexao abriria um banco novo e vazio e o teste quebraria
#  com "tabela nao existe")
from sqlalchemy.pool import StaticPool

# get_db = a "tomada do banco" original que o app usa em producao
from app.database import Base, get_db
# app = a aplicacao FastAPI inteira (rotas, CORS, tudo) ja montada
from app.main import app

# sqlite:// (sem caminho de arquivo) = banco em memória, vive só enquanto o pytest roda
engine = create_engine(
    'sqlite://',
    # check_same_thread= False = deixa o TesteClient usar o banco de qualquer thread
    # (o TestClient roda o app em outra thread e sem isso SQLite reclamaria)
    connect_args = {'check_same_thread': False},
    # StaticPool = sempre a MESMA conexão -> o mesmo banco em memória compartilhado
    poolclass = StaticPool,
)

# Fabrica de sessões do banco deteste (mesmo modelo do app.database)
TestingSessionLocal = sessionmaker(bind = engine, autoflush = False, autocommit = False)

# A 'tomada' que os testes vão usar no lugar da real
def get_db_teste():
    db = TestingSessionLocal()
    try:
        yield db        # entrega a sessão pro endpoint usar
    finally:
        db.close()      # devolve/fecha no fim (igual o get_db original)

# fixture = 'cenário' reutilizável: todo teste que pedir 'client' recebe este objeto já pronto
# montado ANTES do teste e desmontado DEPOIS
@pytest.fixture()
def client():

    # Cria as 11 tabelas do zero neste banco em memória
    Base.metadata.create_all(engine)

    # Troca de tomada: a partir daqui, Depends(get_db) devolve o banco de teste
    app.dependency_overrides[get_db] = get_db_teste

    # TestClient = 'usuario fake' fazendo HTTP pro nosso app (GET/POST etc)
    with TestClient(app) as c:
        yield c     # o teste roda aqui, usando 'c'

    # Depois do teste: desliga a troca e apaga as tabelas > o próximo teste começa limpo
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)

