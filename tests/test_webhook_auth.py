import sys
import types
import unittest

# Stubs mínimos (mesmo padrão dos outros testes) para importar o server
# sem precisar das dependências externas (Flask/dotenv).
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
    path="/", method="GET", form={}, json={}, args={}, headers={}, remote_addr="127.0.0.1",
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


class WebhookOriginValidationTest(unittest.TestCase):
    """Cobre o rollout em 2 estágios da validação de origem do webhook."""

    def setUp(self):
        # Guarda o estado original dos globais que os testes alteram.
        self._secret = server.WEBHOOK_SECRET
        self._enforce = server.WEBHOOK_SECRET_ENFORCE

    def tearDown(self):
        server.WEBHOOK_SECRET = self._secret
        server.WEBHOOK_SECRET_ENFORCE = self._enforce

    # --- Estágio 0: sem secret configurado (comportamento de hoje) ---
    def test_sem_secret_aceita_qualquer_request(self):
        server.WEBHOOK_SECRET = ""
        server.WEBHOOK_SECRET_ENFORCE = False
        ok, motivo = server.validar_origem_webhook({})
        self.assertTrue(ok)
        self.assertEqual(motivo, "secret_nao_configurado")

    # --- Estágio 1: secret setado, modo auditoria (nunca derruba) ---
    def test_auditoria_aceita_mesmo_com_secret_errado(self):
        server.WEBHOOK_SECRET = "supersecreto"
        server.WEBHOOK_SECRET_ENFORCE = False
        ok, motivo = server.validar_origem_webhook({"X-Webhook-Secret": "errado"})
        self.assertTrue(ok)
        self.assertEqual(motivo, "audit_mismatch")

    def test_auditoria_aceita_sem_nenhum_header(self):
        server.WEBHOOK_SECRET = "supersecreto"
        server.WEBHOOK_SECRET_ENFORCE = False
        ok, motivo = server.validar_origem_webhook({})
        self.assertTrue(ok)
        self.assertEqual(motivo, "audit_mismatch")

    def test_auditoria_reporta_match_quando_secret_confere(self):
        server.WEBHOOK_SECRET = "supersecreto"
        server.WEBHOOK_SECRET_ENFORCE = False
        ok, motivo = server.validar_origem_webhook({"X-Webhook-Secret": "supersecreto"})
        self.assertTrue(ok)
        self.assertEqual(motivo, "match")

    # --- Estágio 2: enforce ligado ---
    def test_enforce_rejeita_secret_errado(self):
        server.WEBHOOK_SECRET = "supersecreto"
        server.WEBHOOK_SECRET_ENFORCE = True
        ok, motivo = server.validar_origem_webhook({"X-Webhook-Secret": "errado"})
        self.assertFalse(ok)
        self.assertEqual(motivo, "secret_invalido")

    def test_enforce_rejeita_sem_header(self):
        server.WEBHOOK_SECRET = "supersecreto"
        server.WEBHOOK_SECRET_ENFORCE = True
        ok, motivo = server.validar_origem_webhook({})
        self.assertFalse(ok)
        self.assertEqual(motivo, "secret_invalido")

    def test_enforce_aceita_secret_correto(self):
        server.WEBHOOK_SECRET = "supersecreto"
        server.WEBHOOK_SECRET_ENFORCE = True
        ok, motivo = server.validar_origem_webhook({"X-Webhook-Secret": "supersecreto"})
        self.assertTrue(ok)
        self.assertEqual(motivo, "match")

    # --- Extração do secret de diferentes headers ---
    def test_le_secret_do_header_apikey(self):
        server.WEBHOOK_SECRET = "supersecreto"
        server.WEBHOOK_SECRET_ENFORCE = True
        ok, motivo = server.validar_origem_webhook({"apikey": "supersecreto"})
        self.assertTrue(ok)
        self.assertEqual(motivo, "match")

    def test_le_secret_do_authorization_bearer(self):
        server.WEBHOOK_SECRET = "supersecreto"
        server.WEBHOOK_SECRET_ENFORCE = True
        ok, motivo = server.validar_origem_webhook({"Authorization": "Bearer supersecreto"})
        self.assertTrue(ok)
        self.assertEqual(motivo, "match")

    # --- Máscara nunca vaza o segredo inteiro ---
    def test_mascara_nao_expoe_segredo_inteiro(self):
        mascarado = server._mascarar_segredo("supersecreto")
        self.assertNotIn("supersecreto", mascarado)
        self.assertIn("len=", mascarado)
        self.assertEqual(server._mascarar_segredo(""), "(vazio)")


if __name__ == "__main__":
    unittest.main()
