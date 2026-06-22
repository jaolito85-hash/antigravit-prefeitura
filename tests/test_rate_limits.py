"""Testes das políticas de rate limit e da correção de concorrência (#4).

Cobre:
- Concorrência: contadores sob lock não perdem contagem (race) com várias threads.
- Políticas: limite diário, burst (ok→estourou→cooldown), áudio hora/dia.
"""
import sys
import threading
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


class ConcurrencyCounterTest(unittest.TestCase):
    """O lock garante que o contador nunca libere mais que o limite (sem race)."""

    def test_rate_limit_nao_perde_contagem_sob_threads(self):
        jid = "55440000race@s.whatsapp.net"
        server.rate_limit_store.pop(jid, None)
        n_threads = 50
        liberados = []
        barrier = threading.Barrier(n_threads)

        def worker():
            barrier.wait()  # maximiza a disputa simultânea
            if not server.is_rate_limited(jid):
                liberados.append(1)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exatamente RATE_LIMIT_MAX podem passar; o resto é barrado. Sem lock,
        # o read-modify-write concorrente deixaria passar mais que o limite.
        self.assertEqual(sum(liberados), server.RATE_LIMIT_MAX)

    def test_daily_limit_nao_perde_contagem_sob_threads(self):
        jid = "55440000raceday@s.whatsapp.net"
        server.daily_limit_store.pop(jid, None)
        n_threads = 60
        liberados = []
        barrier = threading.Barrier(n_threads)

        def worker():
            barrier.wait()
            if not server.is_daily_limited(jid):
                liberados.append(1)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(sum(liberados), server.DAILY_LIMIT_MAX)


class DailyLimitPolicyTest(unittest.TestCase):
    def test_limite_diario_default_25(self):
        self.assertEqual(server.DAILY_LIMIT_MAX, 25)

    def test_bloqueia_apos_o_limite(self):
        jid = "5544daily@s.whatsapp.net"
        server.daily_limit_store.pop(jid, None)
        liberados = sum(0 if server.is_daily_limited(jid) else 1 for _ in range(server.DAILY_LIMIT_MAX + 5))
        self.assertEqual(liberados, server.DAILY_LIMIT_MAX)


class BurstPolicyTest(unittest.TestCase):
    def setUp(self):
        self.jid = "5544burst@s.whatsapp.net"
        server.burst_limit_store.pop(self.jid, None)
        server.burst_cooldown_until.pop(self.jid, None)

    def tearDown(self):
        server.burst_limit_store.pop(self.jid, None)
        server.burst_cooldown_until.pop(self.jid, None)

    def test_sequencia_ok_estourou_cooldown(self):
        # As primeiras BURST_LIMIT_MAX passam.
        for _ in range(server.BURST_LIMIT_MAX):
            self.assertEqual(server.avaliar_burst(self.jid), "ok")
        # A próxima estoura (avisa uma vez).
        self.assertEqual(server.avaliar_burst(self.jid), "estourou")
        # As seguintes ficam em cooldown silencioso.
        self.assertEqual(server.avaliar_burst(self.jid), "cooldown")

    def test_burst_max_default_5(self):
        self.assertEqual(server.BURST_LIMIT_MAX, 5)


class AudioPolicyTest(unittest.TestCase):
    def test_audio_max_seconds_default_60(self):
        self.assertEqual(server.AUDIO_MAX_SECONDS, 60)

    def test_audio_hora_default_3(self):
        jid = "5544audh@s.whatsapp.net"
        server.audio_limit_store.pop(jid, None)
        liberados = sum(0 if server.is_audio_limited(jid) else 1 for _ in range(server.AUDIO_LIMIT_MAX + 3))
        self.assertEqual(liberados, server.AUDIO_LIMIT_MAX)

    def test_audio_dia_default_10(self):
        self.assertEqual(server.AUDIO_DAILY_MAX, 10)
        jid = "5544audd@s.whatsapp.net"
        server.audio_daily_store.pop(jid, None)
        liberados = sum(0 if server.is_audio_daily_limited(jid) else 1 for _ in range(server.AUDIO_DAILY_MAX + 4))
        self.assertEqual(liberados, server.AUDIO_DAILY_MAX)


if __name__ == "__main__":
    unittest.main()
