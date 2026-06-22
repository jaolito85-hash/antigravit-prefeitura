"""Testes do gate do pré-filtro de moderação por IA.

Canal de RECLAMAÇÕES: criticar a prefeitura, reclamar de vizinho, demonstrar
frustração ou usar tom ríspido NUNCA pode ser bloqueado. Só conteúdo sexual
bloqueia no pré-filtro; o resto segue (palavrão tem o filtro de keywords que só
avisa; ameaça real vira handoff sensível).
"""
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


class AiModerationGateTest(unittest.TestCase):
    JID = "554499999999@s.whatsapp.net"

    def _res(self, category, inappropriate=True):
        return {"inappropriate": inappropriate, "category": category, "reason": "teste"}

    def test_caso_do_bug_abuse_nao_bloqueia(self):
        # "Terreno do vizinho cheio de lixo e ninguem da prefeitura faz nada" → abuse (errado).
        self.assertIsNone(server.handle_ai_moderation(self.JID, "ninguem da prefeitura faz nada", self._res("abuse")))

    def test_spam_nao_bloqueia(self):
        self.assertIsNone(server.handle_ai_moderation(self.JID, "...", self._res("spam")))

    def test_threat_nao_bloqueia_no_prefiltro(self):
        # Ameaça real é tratada como handoff sensível adiante, não bloqueada aqui.
        self.assertIsNone(server.handle_ai_moderation(self.JID, "...", self._res("threat")))

    def test_injection_nao_bloqueia(self):
        self.assertIsNone(server.handle_ai_moderation(self.JID, "...", self._res("injection")))

    def test_ok_nao_bloqueia(self):
        self.assertIsNone(server.handle_ai_moderation(self.JID, "...", self._res("ok", inappropriate=False)))

    def test_resultado_vazio_nao_bloqueia(self):
        self.assertIsNone(server.handle_ai_moderation(self.JID, "...", None))

    def test_sexual_esta_na_lista_de_acao(self):
        # Conteúdo sexual continua sendo a única categoria que bloqueia no pré-filtro.
        self.assertEqual(server.ACAO_MODERACAO_CATEGORIAS, {"sexual"})


if __name__ == "__main__":
    unittest.main()
