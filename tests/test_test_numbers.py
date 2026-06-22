"""Testes do modo 'número de teste' (oculto do painel da Prefeitura).

Mensagens de números de teste são atendidas normalmente, mas os cards não
aparecem em nenhuma tela do painel — tudo passa por get_feedbacks().
"""
import sys
import types
import unittest
from unittest.mock import patch

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


# Fake mínimo do cliente Supabase só para get_feedbacks (select().order().execute()).
class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def select(self, *a, **k):
        return self

    def order(self, *a, **k):
        return self

    def execute(self):
        return _FakeResult(list(self._rows))


class _FakeSupabase:
    def __init__(self, rows):
        self._rows = rows

    def table(self, name):
        return _FakeQuery(self._rows)


class TestNumberMatchingTest(unittest.TestCase):
    def setUp(self):
        self._orig = server.TEST_NUMBERS_SUFIXOS
        # Número de teste informado pelo usuário (com o 9º dígito).
        server.TEST_NUMBERS_SUFIXOS = {server._so_digitos("44991546866")[-8:]}

    def tearDown(self):
        server.TEST_NUMBERS_SUFIXOS = self._orig

    def test_casa_formato_armazenado_sem_o_nono_digito(self):
        # Como o WhatsApp armazenou (sem o 9 extra) — deve casar.
        self.assertTrue(server.is_test_number("554491546866@s.whatsapp.net"))

    def test_casa_numero_cru_com_nono_digito(self):
        self.assertTrue(server.is_test_number("5544991546866@s.whatsapp.net"))

    def test_numero_diferente_nao_casa(self):
        self.assertFalse(server.is_test_number("554488556944@s.whatsapp.net"))

    def test_sender_vazio_nao_casa(self):
        self.assertFalse(server.is_test_number(""))
        self.assertFalse(server.is_test_number(None))


class TestNumberFilteringTest(unittest.TestCase):
    def setUp(self):
        self._orig = server.TEST_NUMBERS_SUFIXOS
        server.TEST_NUMBERS_SUFIXOS = {server._so_digitos("44991546866")[-8:]}

    def tearDown(self):
        server.TEST_NUMBERS_SUFIXOS = self._orig

    def test_ocultar_remove_apenas_o_de_teste(self):
        cards = [
            {"id": 1, "sender": "554491546866@s.whatsapp.net", "message": "teste"},
            {"id": 2, "sender": "554488556944@s.whatsapp.net", "message": "real"},
        ]
        visiveis = server._ocultar_numeros_teste(cards)
        ids = [c["id"] for c in visiveis]
        self.assertEqual(ids, [2])

    def test_get_feedbacks_exclui_numero_de_teste(self):
        cards = [
            {"id": 1, "sender": "554491546866@s.whatsapp.net", "message": "teste"},
            {"id": 2, "sender": "554488556944@s.whatsapp.net", "message": "real"},
            {"id": 3, "sender": "554499990000@s.whatsapp.net", "message": "real2"},
        ]
        with patch.object(server, "get_supabase", return_value=_FakeSupabase(cards)):
            visiveis = server.get_feedbacks()
        ids = sorted(c["id"] for c in visiveis)
        self.assertEqual(ids, [2, 3])

    def test_sem_numeros_de_teste_nao_filtra_nada(self):
        server.TEST_NUMBERS_SUFIXOS = set()
        cards = [{"id": 1, "sender": "554491546866@s.whatsapp.net"}]
        self.assertEqual(server._ocultar_numeros_teste(cards), cards)


if __name__ == "__main__":
    unittest.main()
