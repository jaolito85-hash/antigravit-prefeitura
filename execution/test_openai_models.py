"""Smoke-test dos modelos OpenAI configurados no .env.

Chama o wrapper real openai_chat_completion() do server.py (mesmo caminho da
produção) para cada variável de modelo de chat, e a Moderation API. Útil para
validar uma troca de modelo ANTES do deploy.

Uso:
    python execution/test_openai_models.py
"""
import os
import sys
import time

# Garante que o server.py (raiz do repo) seja importável rodando de qualquer pasta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()  # precisa vir antes do import do server (ele lê env no import)

import server  # noqa: E402


def _mask(key: str) -> str:
    """Mostra só o suficiente da chave para conferência, sem expor o segredo."""
    return f"{key[:7]}...{key[-4:]}" if key and len(key) > 15 else "(inválida?)"


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "coloque_sua_chave_aqui":
        print("ERRO: defina OPENAI_API_KEY no .env antes de rodar.")
        return 1
    print(f"Chave: {_mask(api_key)}")

    client = server.get_openai_client()
    if client is None:
        print("ERRO: não foi possível criar o cliente OpenAI (SDK/chave).")
        return 1

    chat_targets = [
        ("OPENAI_MODEL_CITIZEN_REPLY", server.OPENAI_MODEL_CITIZEN_REPLY),
        ("OPENAI_MODEL_CLASSIFIER", server.OPENAI_MODEL_CLASSIFIER),
        ("OPENAI_MODEL_INTERNAL_DRAFT", server.OPENAI_MODEL_INTERNAL_DRAFT),
    ]
    failures = 0

    for var_name, model in chat_targets:
        print(f"\n=== {var_name} = {model} ===")
        start = time.time()
        try:
            # temperature customizada de propósito: exercita a remoção feita
            # pelo wrapper para modelos gpt-5* (senão a API devolveria 400)
            response = server.openai_chat_completion(
                client,
                model=model,
                messages=[
                    {"role": "system", "content": "Responda em uma frase curta, em português."},
                    {"role": "user", "content": "Diga apenas: teste de migração OK."},
                ],
                max_tokens=50,
                temperature=0.5,
                timeout=30,
            )
            elapsed_ms = int((time.time() - start) * 1000)
            choice = response.choices[0]
            text = (choice.message.content or "").strip()
            print(f"OK  {elapsed_ms}ms  finish_reason={choice.finish_reason}")
            print(f"Resposta: {text[:200]}")
            if not text:
                print("FALHA: resposta vazia (orçamento de tokens consumido pelo raciocínio?)")
                failures += 1
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            print(f"FALHA  {elapsed_ms}ms  {type(e).__name__}: {e}")
            failures += 1

    moderation_model = server.OPENAI_MODEL_MODERATION
    print(f"\n=== OPENAI_MODEL_MODERATION = {moderation_model} ===")
    start = time.time()
    try:
        result = client.moderations.create(
            model=moderation_model,
            input="mensagem neutra de teste",
            timeout=15,
        )
        elapsed_ms = int((time.time() - start) * 1000)
        flagged = result.results[0].flagged
        print(f"OK  {elapsed_ms}ms  flagged={flagged}")
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        print(f"FALHA  {elapsed_ms}ms  {type(e).__name__}: {e}")
        failures += 1

    print(f"\n{'TUDO OK' if failures == 0 else f'{failures} FALHA(S)'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
