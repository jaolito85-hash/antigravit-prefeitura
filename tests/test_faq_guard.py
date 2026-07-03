"""Testes das correções de segurança/fluxo (PENDENCIAS itens 9, 10):
- FAQ só responde pergunta curta de informação — reclamação segue para virar card.
- Chave admin aceita SÓ por header (X-Admin-Key); query string não autentica mais.
"""
import os
import sys
import types
import unittest

# --- Stubs de ambiente (mesma abordagem dos outros testes) ---
flask_stub = types.ModuleType("flask")


class FakeFlask:
    def __init__(self, *args, **kwargs):
        self.config = {}
        self.secret_key = None
        self.permanent_session_lifetime = None

    def route(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator


flask_stub.Flask = FakeFlask
flask_stub.request = types.SimpleNamespace(
    path="/", method="GET", form={}, json={}, args={}, headers={}, remote_addr="127.0.0.1"
)
flask_stub.jsonify = lambda *args, **kwargs: {"args": args, "kwargs": kwargs}
flask_stub.render_template = lambda *args, **kwargs: ""
flask_stub.redirect = lambda target: target
flask_stub.url_for = lambda endpoint: endpoint
flask_stub.session = {}
sys.modules.setdefault("flask", flask_stub)

dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda *args, **kwargs: None
sys.modules.setdefault("dotenv", dotenv_stub)

import server


class FaqRespondePerguntaCurtaTest(unittest.TestCase):
    """Pergunta curta de informação DEVE receber resposta de FAQ."""

    def test_horario_prefeitura(self):
        self.assertIsNotNone(server.check_faq("qual o horario da prefeitura?"))

    def test_termo_seco_coleta(self):
        self.assertIsNotNone(server.check_faq("coleta de lixo"))

    def test_quando_passa_o_lixo(self):
        self.assertIsNotNone(server.check_faq("quando passa o lixo?"))

    def test_numero_policia(self):
        self.assertIsNotNone(server.check_faq("numero da policia"))

    def test_samu(self):
        self.assertIsNotNone(server.check_faq("samu"))


class FaqNaoEngoleReclamacaoTest(unittest.TestCase):
    """Reclamação contendo termo de FAQ NÃO pode receber FAQ — precisa virar card."""

    def test_coleta_nao_passa(self):
        # Caso real do achado 2026-06-22: respondia horário da coleta e perdia a demanda.
        self.assertIsNone(server.check_faq("a coleta de lixo não passa há 2 semanas"))

    def test_coleta_nao_veio(self):
        self.assertIsNone(server.check_faq("a coleta de lixo não veio essa semana"))

    def test_mensagem_longa_e_contexto(self):
        texto = (
            "boa tarde, queria saber o que aconteceu porque a coleta de lixo "
            "aqui do meu bairro está toda bagunçada já faz um tempo"
        )
        self.assertIsNone(server.check_faq(texto))

    def test_policia_com_ocorrencia(self):
        self.assertIsNone(server.check_faq("chamei a policia e roubaram minha bicicleta"))

    def test_samu_nao_atendeu(self):
        self.assertIsNone(server.check_faq("o samu não atendeu ninguém ontem"))

    def test_faq_key_com_marcador_de_problema(self):
        self.assertIsNone(server.check_faq("coleta de lixo com problema"))

    def test_vazio(self):
        self.assertIsNone(server.check_faq(""))


class AdminKeyHeaderOnlyTest(unittest.TestCase):
    """Chave admin: query string (?key=) não autentica mais; só o header X-Admin-Key."""

    def setUp(self):
        os.environ["ADMIN_KEY"] = "chave-teste-admin"
        self._request = server.request

    def tearDown(self):
        os.environ.pop("ADMIN_KEY", None)
        self._request.headers = {}
        self._request.args = {}

    def _status(self, retorno):
        """Extrai o status HTTP: rota devolve tupla (corpo, status) ou só corpo (=200)."""
        if isinstance(retorno, tuple):
            return retorno[1]
        return 200

    def test_query_string_recebe_401(self):
        self._request.headers = {}
        self._request.args = {"key": "chave-teste-admin"}
        self.assertEqual(self._status(server.debug_env()), 401)

    def test_header_correto_autentica(self):
        self._request.headers = {"X-Admin-Key": "chave-teste-admin"}
        self._request.args = {}
        self.assertEqual(self._status(server.debug_env()), 200)

    def test_header_errado_recebe_401(self):
        self._request.headers = {"X-Admin-Key": "chave-errada"}
        self._request.args = {}
        self.assertEqual(self._status(server.debug_env()), 401)

    def test_sem_admin_key_configurada_recebe_401(self):
        os.environ.pop("ADMIN_KEY", None)
        self._request.headers = {"X-Admin-Key": "qualquer"}
        self.assertEqual(self._status(server.debug_env()), 401)


if __name__ == "__main__":
    unittest.main()
