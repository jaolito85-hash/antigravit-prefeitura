"""Testes da persistência de feedbacks (PENDENCIAS #2 — perda silenciosa).

Cobre:
- id/protocolo vindos da coluna identity do Postgres (lidos do insert), nunca
  calculados na aplicação → sem corrida nem colisão de protocolo.
- Supabase fora: demanda vai pro buffer local com flag pending_sync + ALERTA.
- Reconciliação: pendências são reenviadas quando o banco volta.
"""
import io
import os
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from datetime import datetime
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


# --- Fake do cliente Supabase (cadeia table().insert/update/select().execute()) ---
class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeTable:
    def __init__(self, store, fail_insert=False):
        self.store = store          # {'rows': [...], 'next_id': int}
        self.fail_insert = fail_insert
        self._op = None
        self._payload = None
        self._filters = {}

    def insert(self, data):
        self._op, self._payload = "insert", data
        return self

    def update(self, updates):
        self._op, self._payload = "update", updates
        return self

    def select(self, *a, **k):
        self._op = "select"
        return self

    def eq(self, col, val):
        self._filters[col] = val
        return self

    def order(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def execute(self):
        if self._op == "insert":
            if self.fail_insert:
                raise RuntimeError("supabase indisponivel")
            row = dict(self._payload)
            # Simula a coluna identity: o BANCO gera o id, não a aplicação.
            row["id"] = self.store["next_id"]
            self.store["next_id"] += 1
            self.store["rows"].append(row)
            return _FakeResult([row])
        if self._op == "update":
            atualizadas = []
            for r in self.store["rows"]:
                if all(r.get(k) == v for k, v in self._filters.items()):
                    r.update(self._payload)
                    atualizadas.append(r)
            return _FakeResult(atualizadas)
        if self._op == "select":
            return _FakeResult(list(self.store["rows"]))
        return _FakeResult([])


class FakeSupabase:
    def __init__(self, next_id=1, fail_insert=False):
        self.store = {"rows": [], "next_id": next_id}
        self.fail_insert = fail_insert

    def table(self, name):
        return _FakeTable(self.store, self.fail_insert)


class FeedbackPersistenceTest(unittest.TestCase):
    def setUp(self):
        # Aponta o buffer local para um arquivo temporário isolado.
        self._tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self._tmp.close()
        os.unlink(self._tmp.name)  # começa inexistente
        self._events_orig = server.EVENTS_FILE
        server.EVENTS_FILE = self._tmp.name
        # Captura stdout em memória: os prints do server usam emojis (✅/🚨), que
        # o console cp1252 do Windows não codifica. StringIO é encoding-agnóstico.
        self._stdout_ctx = redirect_stdout(io.StringIO())
        self._stdout_ctx.__enter__()

    def tearDown(self):
        self._stdout_ctx.__exit__(None, None, None)
        server.EVENTS_FILE = self._events_orig
        if os.path.exists(self._tmp.name):
            os.unlink(self._tmp.name)

    def _report(self, sender="554499999999@s.whatsapp.net"):
        return {
            "sender": sender,
            "name": "Cidadão",
            "message": "Buraco na rua",
            "status": "aberto",
            "category": "Infraestrutura & Obras",
        }

    # --- id/protocolo vêm do banco (sem corrida/colisão) ---
    def test_save_usa_id_do_banco_e_monta_protocolo(self):
        with patch.object(server, "get_supabase", return_value=FakeSupabase(next_id=43)):
            saved = server.save_feedback(self._report())
        ano = datetime.utcnow().year
        self.assertEqual(saved["id"], 43)
        self.assertEqual(saved["protocol"], f"{ano}0043")
        self.assertTrue(saved["synced"])

    def test_id_explicito_passado_e_ignorado(self):
        # Mesmo se o chamador mandar id/protocol, o banco (identity) decide.
        fake = FakeSupabase(next_id=10)
        report = self._report()
        report["id"] = 1
        report["protocol"] = "20260001"
        with patch.object(server, "get_supabase", return_value=fake):
            saved = server.save_feedback(report)
        self.assertEqual(saved["id"], 10)
        self.assertEqual(saved["protocol"], f"{datetime.utcnow().year}0010")
        # O protocolo foi gravado na linha do banco (update pós-insert).
        self.assertEqual(fake.store["rows"][0]["protocol"], saved["protocol"])

    def test_feedbacks_sequenciais_nao_colidem(self):
        fake = FakeSupabase(next_id=1)
        with patch.object(server, "get_supabase", return_value=fake):
            a = server.save_feedback(self._report("A@s.whatsapp.net"))
            b = server.save_feedback(self._report("B@s.whatsapp.net"))
        self.assertNotEqual(a["id"], b["id"])
        self.assertNotEqual(a["protocol"], b["protocol"])

    # --- Supabase fora: buffer local + alerta, sem perda silenciosa ---
    def test_supabase_indisponivel_salva_pendente_e_alerta(self):
        with patch.object(server, "get_supabase", return_value=None):
            buf = io.StringIO()
            with redirect_stdout(buf):
                saved = server.save_feedback(self._report())
        self.assertFalse(saved["synced"])
        self.assertTrue(saved["protocol"])
        self.assertEqual(server.contar_pendentes(), 1)
        self.assertIn("DEMANDA-NAO-SINCRONIZADA", buf.getvalue())
        # A demanda ficou marcada como pendente no buffer.
        linhas = server.load_json(server.EVENTS_FILE, [])
        self.assertTrue(linhas[0]["pending_sync"])

    def test_insert_falha_e_reconnect_falha_cai_no_buffer(self):
        fail = FakeSupabase(fail_insert=True)
        with patch.object(server, "get_supabase", return_value=fail), \
             patch.object(server, "_reconnect_supabase", return_value=None):
            saved = server.save_feedback(self._report())
        self.assertFalse(saved["synced"])
        self.assertEqual(server.contar_pendentes(), 1)

    # --- Reconciliação quando o banco volta ---
    def test_flush_reenvia_pendentes(self):
        # Simula um pendente deixado por um outage anterior.
        with patch.object(server, "get_supabase", return_value=None):
            server.save_feedback(self._report())
        self.assertEqual(server.contar_pendentes(), 1)

        fake = FakeSupabase(next_id=100)
        with patch.object(server, "get_supabase", return_value=fake):
            reenviados = server.flush_pending_feedbacks(fake)
        self.assertEqual(reenviados, 1)
        self.assertEqual(server.contar_pendentes(), 0)
        # Protocolo informado ao cidadão é preservado no banco.
        self.assertEqual(len(fake.store["rows"]), 1)
        self.assertTrue(fake.store["rows"][0]["protocol"])
        self.assertNotIn("pending_sync", fake.store["rows"][0])

    def test_save_com_banco_saudavel_reconcilia_pendentes(self):
        # Deixa 1 pendente do "outage".
        with patch.object(server, "get_supabase", return_value=None):
            server.save_feedback(self._report("antigo@s.whatsapp.net"))
        self.assertEqual(server.contar_pendentes(), 1)

        # Banco volta: o próximo save deve gravar o novo E drenar o pendente.
        fake = FakeSupabase(next_id=200)
        with patch.object(server, "get_supabase", return_value=fake):
            saved = server.save_feedback(self._report("novo@s.whatsapp.net"))
        self.assertTrue(saved["synced"])
        self.assertEqual(server.contar_pendentes(), 0)
        self.assertEqual(len(fake.store["rows"]), 2)  # novo + pendente reconciliado

    # --- Helpers ---
    def test_montar_protocolo_formato(self):
        ano = datetime.utcnow().year
        self.assertEqual(server.montar_protocolo(42), f"{ano}0042")
        self.assertEqual(server.montar_protocolo(12345), f"{ano}12345")

    def test_contar_pendentes_so_conta_pending(self):
        server.save_json(server.EVENTS_FILE, [
            {"id": 1, "pending_sync": True},
            {"id": 2},
            {"id": 3, "pending_sync": True},
        ])
        self.assertEqual(server.contar_pendentes(), 2)


if __name__ == "__main__":
    unittest.main()
