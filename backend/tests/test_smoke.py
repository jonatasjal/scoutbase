# Teste de "fumaca": "a API esta viva?" — o mais basico possivel.
# Serve pra provar que o setup (conftest + fixture client) esta funcionando
# antes de escrevermos testes de verdade.

def test_health_response_ok(client):
    # client = fixture do conftest: um GET /health de verdade, mas sem rede
    resposta = client.get('/health')
    # 200 = deu certo; json() = corpo da resposta, que é {'status': 'ok'}
    assert resposta.status_code == 200
    assert resposta.json() == {'status': 'ok'}