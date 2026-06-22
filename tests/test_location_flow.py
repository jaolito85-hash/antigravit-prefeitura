"""Testes do fluxo de coleta de endereço (multi-turno).

Cobre o bug: o cidadão informa rua/bairro e o bot precisa (a) reconhecer que a
Clara estava pedindo endereço, (b) entender o bairro, (c) ao completar, enviar o
PROTOCOLO. Antes: bot repetia empatia e não abria protocolo.
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


class WaitingForLocationTest(unittest.TestCase):
    def _msg_com_resposta_da_clara(self, texto_clara):
        # Monta um chamado cuja última fala da Clara é texto_clara.
        m = server.build_feedback_message("a fila na upa esta gigante", "2026-01-01T00:00:00")
        return server.append_conversation_entry(m, "agent", texto_clara)

    def test_reconhece_pedido_rua_barra_bairro(self):
        # Caso do bug: a Clara perguntou "rua/bairro onde ocorreu?".
        msg = self._msg_com_resposta_da_clara("Pode me informar rua/bairro onde ocorreu?")
        self.assertTrue(server.is_waiting_for_location(msg))

    def test_reconhece_pergunta_generica_com_bairro(self):
        msg = self._msg_com_resposta_da_clara("Pode me informar o seu bairro ou rua, por favor?")
        self.assertTrue(server.is_waiting_for_location(msg))

    def test_rede_seguranca_pergunta_com_endereco(self):
        msg = self._msg_com_resposta_da_clara("Qual o endereço exato?")
        self.assertTrue(server.is_waiting_for_location(msg))

    def test_nao_marca_quando_clara_nao_perguntou_local(self):
        msg = self._msg_com_resposta_da_clara("Obrigado pelo retorno positivo!")
        self.assertFalse(server.is_waiting_for_location(msg))


class DetectLocationTest(unittest.TestCase):
    def test_centro_e_reconhecido_como_bairro(self):
        has_street, has_hood, region = server.detect_location_components("foi na upa do centro")
        self.assertTrue(has_hood)
        self.assertEqual(region, "Centro")

    def test_rua_com_bairro_completo(self):
        has_street, has_hood, region = server.detect_location_components("Rua sao paulo, centro")
        self.assertTrue(has_street)
        self.assertTrue(has_hood)


class AnexarProtocoloTest(unittest.TestCase):
    def test_anexa_protocolo_ao_completar(self):
        active = {"protocol": "20260037", "message": server.build_feedback_message("fila na upa", "2026-01-01T00:00:00")}
        out = server.anexar_protocolo_se_completo("Perfeito, anotei o endereço!", active, "completo")
        self.assertIn("📋 Protocolo:\n*20260037*", out)
        self.assertIn(server.ASSINATURA_RODAPE, out)

    def test_nao_anexa_se_ainda_pendente(self):
        active = {"protocol": "20260037", "message": "x"}
        out = server.anexar_protocolo_se_completo("Pode informar o bairro?", active, "pendente")
        self.assertNotIn("Protocolo", out)

    def test_nao_repete_se_ja_enviado(self):
        # A mensagem do chamado já contém o protocolo de um envio anterior.
        active = {"protocol": "20260037", "message": "...📋 Protocolo:\n*20260037*..."}
        out = server.anexar_protocolo_se_completo("Perfeito!", active, "completo")
        self.assertEqual(out, "Perfeito!")

    def test_build_location_followup_completo_e_curto(self):
        # Quando completo, o corpo é curto (a assinatura anexada já agradece).
        self.assertNotIn("Seu chamado já foi registrado", server.build_location_followup_reply(True, True))


if __name__ == "__main__":
    unittest.main()
