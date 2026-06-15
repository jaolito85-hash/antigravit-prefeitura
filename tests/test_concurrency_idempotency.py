"""Testes dos guardrails de concorrência e idempotência adicionados para produção.

Cobre o que protege o fluxo do webhook contra reentrega da Evolution e contra
race conditions entre as threads do Gunicorn (1 worker / 4 threads).
"""
import os
import sys
import threading
import time
import types
import unittest

# --- Stubs de ambiente (mesma abordagem de test_security_guardrails.py) ---
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


class IdempotencyTest(unittest.TestCase):
    def setUp(self):
        server._processed_messages.clear()

    def test_primeira_vez_false_depois_true(self):
        # Mesmo evento reenviado pela Evolution não deve ser reprocessado.
        self.assertFalse(server.ja_processado("MSG_ABC"))
        self.assertTrue(server.ja_processado("MSG_ABC"))

    def test_id_vazio_nunca_deduplica(self):
        self.assertFalse(server.ja_processado(""))
        self.assertFalse(server.ja_processado(None))

    def test_ids_distintos_sao_independentes(self):
        self.assertFalse(server.ja_processado("A"))
        self.assertFalse(server.ja_processado("B"))
        self.assertTrue(server.ja_processado("A"))
        self.assertTrue(server.ja_processado("B"))


class JidLockTest(unittest.TestCase):
    def test_mesmo_jid_retorna_mesmo_lock(self):
        jid = "5544999@s.whatsapp.net"
        lock1 = server.acquire_jid_lock(jid)
        lock1.release()
        lock2 = server.acquire_jid_lock(jid)
        lock2.release()
        self.assertIs(lock1, lock2)

    def test_jids_diferentes_ganham_locks_diferentes(self):
        l1 = server.acquire_jid_lock("A@s")
        l2 = server.acquire_jid_lock("B@s")
        try:
            self.assertIsNot(l1, l2)
        finally:
            l1.release()
            l2.release()

    def test_lock_serializa_o_mesmo_jid(self):
        # Quatro threads disputando o mesmo número: nunca podem estar dentro da
        # seção crítica ao mesmo tempo (é o que evita perder texto do cidadão).
        jid = "5544lock@s"
        ordem = []
        estado = {"dentro": 0, "max_simultaneo": 0}
        guard = threading.Lock()

        def worker(tag):
            lk = server.acquire_jid_lock(jid)
            try:
                with guard:
                    estado["dentro"] += 1
                    estado["max_simultaneo"] = max(estado["max_simultaneo"], estado["dentro"])
                time.sleep(0.03)
                ordem.append(tag)
                with guard:
                    estado["dentro"] -= 1
            finally:
                lk.release()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(estado["max_simultaneo"], 1)  # nunca dois ao mesmo tempo
        self.assertEqual(len(ordem), 4)                # todos completaram


class ExtractResponseTextTest(unittest.TestCase):
    def _resp(self, content):
        msg = type("Msg", (), {"content": content})()
        choice = type("Choice", (), {"message": msg})()
        return type("Resp", (), {"choices": [choice]})()

    def test_conteudo_normal(self):
        self.assertEqual(server.extract_response_text(self._resp("  oi  ")), "oi")

    def test_content_none_retorna_vazio(self):
        # OpenAI pode devolver content=None (finish_reason='length'/recusa).
        self.assertEqual(server.extract_response_text(self._resp(None)), "")

    def test_resposta_malformada_retorna_vazio(self):
        bad = type("Resp", (), {"choices": []})()
        self.assertEqual(server.extract_response_text(bad), "")


if __name__ == "__main__":
    unittest.main()
