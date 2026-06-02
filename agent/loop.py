"""Core agent loop: LLM ↔ tool calls, max iterations guard."""
import json

from agent import llm, tools
import memory.store as store

_SYSTEM = """Sei Jarvis, un assistente personale preciso e conciso.
Hai accesso a Gmail, Google Calendar, file locali e una vault Obsidian per la memoria persistente.

Regole operative:
- Per leggere dati (email, eventi, file, note) agisci subito.
- Per scrivere/inviare/modificare email o eventi, usa il tool apposito: verrà chiesta approvazione su Telegram.
- Scrivere note in Obsidian (memory_write/memory_append) è autonomo, non richiede approvazione.
- Rispondi sempre in italiano, in modo chiaro e breve.

Memoria:
- All'inizio di ogni conversazione cerca nella vault se hai già informazioni rilevanti (memory_search).
- Quando apprendi qualcosa di importante sull'utente (preferenze, abitudini, decisioni, persone), salvalo in Obsidian:
    memory_write(title="<argomento>", content="...", folder="Memoria")
- Alla fine di ogni conversazione significativa salva un riassunto:
    memory_append(title="<data-odierna>", content="...", folder="Conversazioni")
- Le note in "Memoria/" sono fatti permanenti. Le note in "Conversazioni/" sono il diario.
"""

MAX_ITER = 10


def run(user_message: str, history: list[dict] | None = None) -> str:
    """Run the agent loop for a single user message. Returns final text reply."""
    messages: list[dict] = [{"role": "system", "content": _SYSTEM}]

    if history:
        messages.extend(history)
    else:
        messages.extend(store.get_history(n=10))

    messages.append({"role": "user", "content": user_message})

    for _ in range(MAX_ITER):
        msg = llm.call(messages, tools=tools.TOOLS)

        # pure text reply → done
        if not msg.get("tool_calls"):
            return msg.get("content") or ""

        # append assistant message with tool_calls
        messages.append(msg)

        # execute each tool call
        for tc in msg["tool_calls"]:
            fn = tc["function"]
            name = fn["name"]
            args = json.loads(fn.get("arguments") or "{}")
            result = tools.execute(name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    return "Raggiunto il limite di iterazioni. Riprova con una richiesta più specifica."
