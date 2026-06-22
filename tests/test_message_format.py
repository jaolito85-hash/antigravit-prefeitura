"""Testes do formato das mensagens ao cidadão (protocolo em negrito + assinatura).

Garante o estilo bonito/espaçado: corpo + bloco de protocolo em negrito (sem #) +
assinatura, separados por linha em branco.
"""
import os
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


def _fake_client_returning(content):
    class FakeChoice:
        message = type("Message", (), {"content": content})()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, api_key=None):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    return FakeClient


class FormatadorTest(unittest.TestCase):
    def test_estrutura_completa(self):
        out = server.formatar_resposta_com_protocolo("Sinto muito pelo ocorrido.", "20260035")
        # Bloco de protocolo em negrito, com o rótulo e SEM '#'.
        self.assertIn("📋 Protocolo:\n*20260035*", out)
        self.assertNotIn("#20260035", out)
        # Assinatura presente.
        self.assertIn(server.ASSINATURA_RODAPE, out)
        # Espaçamento entre os blocos.
        self.assertIn("\n\n", out)
        # Ordem: corpo → protocolo → assinatura.
        self.assertTrue(out.index("Sinto muito") < out.index("Protocolo") < out.index(server.ASSINATURA_RODAPE))

    def test_sem_assinatura(self):
        out = server.formatar_resposta_com_protocolo("Mensagem sensível.", "20260099", com_assinatura=False)
        self.assertIn("*20260099*", out)
        self.assertNotIn(server.ASSINATURA_RODAPE, out)

    def test_sem_protocolo_nao_quebra(self):
        out = server.formatar_resposta_com_protocolo("Só um aviso.", None)
        self.assertIn("Só um aviso.", out)
        self.assertNotIn("Protocolo", out)


class FormatoIntegracaoTest(unittest.TestCase):
    def test_generate_ai_response_usa_novo_formato(self):
        corpo_ia = "Sinto muito pelo buraco. Qual é a rua e o bairro?"
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=False):
            with patch("server.OpenAI", _fake_client_returning(corpo_ia), create=True):
                reply = server.generate_ai_response(
                    "buraco na minha rua",
                    "Infraestrutura & Obras",
                    "Urgente",
                    "20260035",
                    location_status="pendente",
                    remote_jid="554499999999@s.whatsapp.net",
                )
        self.assertIn("📋 Protocolo:\n*20260035*", reply)
        self.assertNotIn("#20260035", reply)
        self.assertIn(server.ASSINATURA_RODAPE, reply)
        self.assertIn("Sinto muito pelo buraco", reply)

    def test_handoff_sensivel_tem_protocolo_negrito_sem_assinatura(self):
        reply = server.build_sensitive_handoff_reply("20260042", "Saúde & Atendimento", reasons=["saude_grave"])
        self.assertIn("*20260042*", reply)
        self.assertNotIn(server.ASSINATURA_RODAPE, reply)  # tom sério: sem assinatura alegre
        self.assertIn("192", reply)  # nota de emergência preservada


if __name__ == "__main__":
    unittest.main()
