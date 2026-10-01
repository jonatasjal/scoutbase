
# ==========================================================================
# É  a fiação elétrica da aplicação com o banco de dados — toda a parte técnica de conectar, consultar e salvar dados:

# 1. create_engine — cria a engine (motor), que é o cano principal da conexão com o Postgres. Ela cuida de: manter conexões abertas (um pool, tipo um pote de conexões prontas para reuso), traduzir suas perguntas para a linguagem do banco, etc. O endereço vem justamente do settings do arquivo anterior.
# 2. sessionmaker — uma fábrica de sessões. Sessão (session) = um cartão de biblioteca: você pega um na entrada (db = SessionLocal()), faz suas leituras e escritas, e devolve no fim (db.close()). Cada operação usa a sua.
#       - autoflush=False — "não envie minhas alterações para o banco automaticamente antes de cada pergunta". Evita que o banco receba mudanças parciais sem você querer.
#       - autocommit=False — "nada é gravado até eu mandar commit()". É o jeito seguro: você revisa e só então confirma (como clicar "Salvar" — sem isso, a mudança é só um rascunho).
# 3. class Base(DeclarativeBase) — uma classe vazia (tipo um formulário em branco) da qual todos os seus models herdam. Exemplo: class Usuario(Base) → o SQLAlchemy lê essa classe e cria a tabela usuario no banco automaticamente. Sem a Base, ele não saberia quais classes viram tabelas.
# ==========================================================================
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass