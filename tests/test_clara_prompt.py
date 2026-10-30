"""Testes do conteúdo dos prompts da Clara e do texto de consentimento.

Não testam o que o modelo responde (isso depende da OpenAI), e sim que as regras
certas chegam ao modelo: persona única nos dois prompts, assistente virtual que
não se passa por humana, instrução de endereço só para problema específico,
Crítico só para risco de vida e consentimento LGPD sem promessa falsa.
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


def _capturar_mensagens(chamada):
    """Roda `chamada` com um cliente OpenAI falso e devolve as mensagens enviadas."""
    captured = {}

    class FakeChoice:
        message = type("Message", (), {"content": "Sinto muito por isso. Encaminhei para a equipe responsável."})()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return FakeResponse()

    class FakeClient:
        def __init__(self, api_key=None):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=False):
        with patch("server.OpenAI", FakeClient, create=True):
            chamada()
    return captured["messages"]


def _prompt_primeira_resposta(urgency="Neutro", category="Iluminação Pública", location_status="pendente"):
    msgs = _capturar_mensagens(lambda: server.generate_ai_response(
        "tem um poste apagado", category, urgency, "20260001",
        location_status=location_status, remote_jid="554499999999@s.whatsapp.net",
    ))
    return msgs[0]["content"]


def _prompt_continuacao():
    msgs = _capturar_mensagens(lambda: server.generate_thread_reply(
        remote_jid="554499999999@s.whatsapp.net",
        text="continua apagado",
        categoria="Iluminação Pública",
        sentimento="Neutro",
        active_feedback={
            "message": server.build_feedback_message("Poste apagado", "2026-01-01T00:00:00"),
            "location_status": "completo",
        },
        new_thread_rua=None,
    ))
    return msgs[0]["content"]


class ClaraPromptTest(unittest.TestCase):
    def test_os_dois_prompts_usam_a_mesma_base(self):
        self.assertIn(server.CLARA_BASE_PROMPT, _prompt_primeira_resposta())
        self.assertIn(server.CLARA_BASE_PROMPT, _prompt_continuacao())

    def test_clara_se_apresenta_como_virtual_e_nao_como_humana(self):
        for prompt in (_prompt_primeira_resposta(), _prompt_continuacao()):
            with self.subTest(prompt=prompt[:40]):
                self.assertIn("assistente virtual", prompt)
                self.assertIn("nunca diga nem dê a entender que é uma pessoa", prompt)
                self.assertNotIn("atendente humana", prompt)

    def test_continuacao_herdou_regras_de_idioma_e_politica(self):
        prompt = _prompt_continuacao()
        self.assertIn("português brasileiro", prompt)
        self.assertIn("política", prompt)

    def test_instrucao_de_endereco_fica_dentro_do_tipo_2(self):
        prompt = _prompt_primeira_resposta(location_status="pendente")
        tipo_2 = prompt.index("2) PROBLEMA ESPECÍFICO")
        tipo_3 = prompt.index("3) ELOGIO")
        endereco = prompt.index("ENDEREÇO: este registro ainda não tem endereço")
        self.assertTrue(tipo_2 < endereco < tipo_3)
        self.assertIn("NÃO peça endereço, mesmo que", prompt)
        self.assertNotIn("INSTRUÇÃO CRÍTICA", prompt)

    def test_categoria_sem_endereco_nao_diz_que_endereco_foi_informado(self):
        prompt = _prompt_primeira_resposta(category="Assistência Social")
        self.assertIn("não precisa de endereço", prompt)
        self.assertNotIn("já foi informado", prompt)

    def test_reclamacao_comum_nao_fala_em_prioridade(self):
        prompt = _prompt_primeira_resposta(urgency="Neutro")
        self.assertIn("Não fale em prioridade", prompt)
        self.assertNotIn("PRIORIDADE MÁXIMA", prompt)

    def test_critico_orienta_telefones_de_emergencia(self):
        prompt = _prompt_primeira_resposta(urgency="Crítico")
        self.assertIn("PRIORIDADE MÁXIMA", prompt)
        self.assertIn("192 (SAMU)", prompt)

    def test_classificador_reserva_critico_para_risco_de_vida(self):
        msgs = _capturar_mensagens(lambda: server.classificar_com_ia("lampada queimada na rua"))
        prompt = msgs[1]["content"]
        self.assertIn("SOMENTE risco à vida", prompt)
        self.assertIn("Lâmpada queimada, buraco, lixo ou falta de remédio NÃO são críticos", prompt)
        self.assertIn("na dúvida entre Neutro e Urgente, escolha Neutro", prompt)


class ConsentimentoTest(unittest.TestCase):
    def test_boas_vindas_nao_promete_falso_sobre_terceiros(self):
        texto = server.normalize_text(server.MENSAGEM_BOAS_VINDAS)
        self.assertNotIn("terceiros", texto)
        self.assertIn("inteligencia artificial", texto)

    def test_boas_vindas_mantem_instrucao_de_sim_e_nao(self):
        self.assertIn("*SIM*", server.MENSAGEM_BOAS_VINDAS)
        self.assertIn("*NÃO*", server.MENSAGEM_BOAS_VINDAS)
        self.assertIn("LGPD", server.MENSAGEM_BOAS_VINDAS)


class CanonizarClassificacaoTest(unittest.TestCase):
    def test_categoria_sem_acento_vira_canonica(self):
        casos = {
            "Administracao & Atendimento": "Administração & Atendimento",
            "Saude & Atendimento": "Saúde & Atendimento",
            "Iluminacao Publica": "Iluminação Pública",
            "Agua & Saneamento": "Água & Saneamento",
            "Limpeza Urbana": "Limpeza Urbana",
        }
        for entrada, esperado in casos.items():
            with self.subTest(entrada=entrada):
                r = server.canonizar_classificacao({"categoria": entrada, "sentimento": "Neutro"})
                self.assertEqual(r["categoria"], esperado)

    def test_categoria_canonica_dispensa_endereco_quando_deve(self):
        r = server.canonizar_classificacao({"categoria": "Administracao & Atendimento"})
        self.assertIn(r["categoria"], server.LOCATION_OPTIONAL_CATEGORIES)

    def test_critico_com_acento_vira_forma_do_painel(self):
        r = server.canonizar_classificacao({"categoria": "Limpeza Urbana", "sentimento": "Crítico"})
        self.assertEqual(r["sentimento"], "Critico")

    def test_entrada_invalida_passa_direto(self):
        self.assertIsNone(server.canonizar_classificacao(None))


class EscalarUrgenciaTest(unittest.TestCase):
    def test_obrigado_nao_vira_reclamacao_em_elogio(self):
        # Caso real (card de teste 40): buraco Neutro + "Obrigado" virou Positivo.
        self.assertEqual(server.escalar_urgencia_do_chamado("Neutro", "Positivo"), (None, None))

    def test_escala_neutro_para_urgente_e_critico(self):
        self.assertEqual(server.escalar_urgencia_do_chamado("Neutro", "Urgente"), ("Urgente", "Negativo"))
        self.assertEqual(server.escalar_urgencia_do_chamado("Urgente", "Critico"), ("Critico", "Negativo"))

    def test_nunca_rebaixa(self):
        self.assertEqual(server.escalar_urgencia_do_chamado("Critico", "Urgente"), (None, None))
        self.assertEqual(server.escalar_urgencia_do_chamado("Urgente", "Neutro"), (None, None))

    def test_critico_com_acento_no_banco_conta_como_critico(self):
        self.assertEqual(server.escalar_urgencia_do_chamado("Crítico", "Urgente"), (None, None))

    def test_elogio_que_vira_reclamacao_grave_escala(self):
        self.assertEqual(server.escalar_urgencia_do_chamado("Positivo", "Urgente"), ("Urgente", "Negativo"))


class AgradecimentoTest(unittest.TestCase):
    def test_agradecimentos_puros_recebem_imagina(self):
        for texto in ["Obrigado", "obrigada!", "Valeu", "vlw", "Muito obrigado 🙏",
                      "ok, obrigada", "Obrigado Clara", "obrigado pela atenção",
                      "Agradeço", "obg", "Tá bom, obrigado!"]:
            with self.subTest(texto=texto):
                self.assertTrue(server.is_agradecimento(texto))

    def test_agradecimento_com_relato_segue_fluxo_normal(self):
        for texto in ["obrigado mas o buraco continua lá",
                      "obrigada, ainda não arrumaram a lâmpada",
                      "valeu, tem outro poste apagado na rua de cima",
                      "", None]:
            with self.subTest(texto=texto):
                self.assertFalse(server.is_agradecimento(texto))

    def test_resposta_e_imagina_com_coracao_azul(self):
        self.assertEqual(server.RESPOSTA_AGRADECIMENTO, "Imagina! 💙")


if __name__ == "__main__":
    unittest.main()
