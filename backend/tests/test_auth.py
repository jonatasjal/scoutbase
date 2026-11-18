# ==========================================================================
# TESTES DE AUTH — o portão de entrada: cadastro, login e token (/auth/me)
#
# Cada teste simula um "usuario fake" batendo na API. Nada de rede/Docker:
# o `client` vem do conftest.py (TestClient + SQLite em memoria, zerado
# a cada teste — por isso o mesmo e-mail pode aparecer em testes diferentes).
# ==========================================================================


# ---------------------------------------------------------------------------
# Helper (funcao de apoio): cadastra uma conta padrao e devolve a resposta.
# "Por que helper?": 6 testes precisam de uma conta criada antes; repetir
# o mesmo POST 6 vezes esconderia o que cada teste realmente quer testar.
# ---------------------------------------------------------------------------
def cadastrar(client, email = 'ana@teste.com', senha = 'senha123'):
    return client.post('/auth/cadastro', json = {
        'nome': 'Ana Teste',
        'email': email,
        'senha': senha,
        'tipo_usuario': 'atleta',   # o enum vai como texto ('atleta', 'olheiro'...)
    })

# ---------------------------------------------------------------------------
# 1) Cadastro feliz: 201 (Criado) + devolve os dados SEM a senha
# ---------------------------------------------------------------------------
def test_cadastro_cria_conta(client):
    resposta = cadastrar(client)

    # 201 = 'algo foi criado' (o endpoint declara status_code = 201)
    assert resposta.status_code == 201
    dados = resposta.json()

    # O id é gerado pelo banco (começa em 1 no banco de teste zerado)
    assert dados['id'] == 1
    assert dados['email'] == 'ana@teste.com'

    # Segurança: a senha NUNCA pode voltar na resposta e nem no hash
    assert 'senha' not in dados
    assert 'senha_hash' not in dados

# ---------------------------------------------------------------------------
# 2) Mesmo e-mail 2 vezes = 409 Conflito (o endpoint checa antes de criar)
# ---------------------------------------------------------------------------
def test_cadastro_duplicado_409(client):
    cadastrar(client)                   # 1ª vez: criou (201)
    resposta = cadastrar(client)        # 2ª vez: mesmo email

    assert resposta.status_code == 409  # 409 = já existe
    # Texto LITERAL do auth.py — o teste é um espelho da resposta real
    assert resposta.json()['detail'] == 'E-mail já cadastrado'

# ---------------------------------------------------------------------------
# 3) Login com a senha certa: 200 + o cracha JWT
# ---------------------------------------------------------------------------
def test_login_ok(client):
    cadastrar(client)
    resposta = client.post('/auth/login', json = {
        'email': 'ana@teste.com',
        'senha': 'senha123',
    })

    assert resposta.status_code == 200
    dados = resposta.json()
    # access_token = o JWT, token_type = 'bearer' (como usá-lo no header)
    assert dados['access_token']        # string não vazia
    assert dados['token_type'] == 'bearer'

# ---------------------------------------------------------------------------
# 4) Login com senha errada: 401
# ---------------------------------------------------------------------------
def test_login_senha_errada_401(client):
    cadastrar(client)
    resposta = client.post('/auth/login', json = {
        'email': 'ana@teste.com',
        'senha': 'senha_errada',
    })

    assert resposta.status_code == 401
    assert resposta.json()['detail'] == 'E-mail ou senha incorretos'

# ---------------------------------------------------------------------------
# 5) Login em e-mail que NAO tem conta: 401 com a MESMA mensagem do teste 4.
#    Por que a mesma? Se fosse "e-mail nao existe", um invasor usaria o
#    login pra descobrir quais emails tem conta no sistema (enumeracao).
# ---------------------------------------------------------------------------
def test_login_email_inexistente_mesma_mensagem(client):
    resposta = client.post('/auth/login', json = {
        'email': 'naoexiste@teste.com',
        'senha': 'senha123',
    })

    assert resposta.status_code == 401
    # Mesmo texto do teste de senha errada — o invasor nao sabe qual dos 2 errou
    assert resposta.json()['detail'] == 'E-mail ou senha incorretos'

# ---------------------------------------------------------------------------
# 6) /auth/me SEM token: 401 (o guarda nem deixa chegar no endpoint)
# ---------------------------------------------------------------------------
def test_me_sem_token_401(client):
    resposta = client.get('/auth/me')      # sem header Authorization

    assert resposta.status_code == 401
    assert resposta.json()['detail'] == 'Token ausente'
   
# ---------------------------------------------------------------------------
# 7) /auth/me com token FORJADO: 401 (assinatura nao bate com a SECRET_KEY)
# ---------------------------------------------------------------------------
def test_me_token_invalido_401(client):
    resposta = client.get(
        '/auth/me',
        headers = {'Authorization': 'Bearer abc.def.ghi'}  # token inventado
    )

    assert resposta.status_code == 401
    # Texto LITERAL do deps.py (com acento no 'inválido')
    assert resposta.json()['detail'] == 'Token inválido ou expirado'

# ---------------------------------------------------------------------------
# 8) Ciclo completo: cadastro -> login -> /auth/me devolve MINHA identidade
# ---------------------------------------------------------------------------
def test_me_com_token_200(client):
    cadastrar(client)
    login = client.post('/auth/login', json = {
        'email': 'ana@teste.com',
        'senha': 'senha123'
    }) 
    token = login.json()['access_token']        # pega só o crachá de dentro

    resposta = client.get(
        '/auth/me',
        # Mesmo formato que o frontend monta: 'Bearer <cracha>' (com ESPACO!)
        headers = {'Authorization': f'Bearer {token}'}
    )

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados['email'] == 'ana@teste.com'
    assert dados['nome'] == 'Ana Teste'
    # atleta_id = None porque a conta nasceu SEM ficha de atleta
    # (a ficha só nasce quando o usuário completa o perfil)
    assert dados['atleta_id'] is None




