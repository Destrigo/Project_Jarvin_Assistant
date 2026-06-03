"""Core agent loop: LLM ↔ tool calls, max iterations guard."""
import json

from agent import llm, tools
import memory.store as store

_SYSTEM = """Sei Jarvis, un assistente personale preciso e conciso.
Hai accesso a Gmail, Google Calendar, file locali e una vault Obsidian strutturata come wiki personale.

## Regole operative
- Per leggere dati (email, eventi, file, note) agisci subito senza chiedere conferma.
- Per scrivere/inviare/modificare email o eventi usa il tool apposito (richiede approvazione Telegram).
- Scrivere/aggiornare note Obsidian è autonomo — non richiede approvazione.
- Rispondi sempre in italiano, in modo chiaro e conciso.

## Struttura della vault Obsidian
La vault è organizzata come una wiki personale composta da:
- **Memoria/**  — fatti permanenti sull'utente (preferenze, persone, progetti, decisioni)
- **Conversazioni/** — diario cronologico (un file per data)
- **Wiki/** — sintesi e pagine tematiche elaborate
- **Fonti/** — documenti originali immutabili (articoli, trascrizioni, note grezze)
- **index.md** — catalogo navigabile di tutta la vault (leggi sempre questo per prima cosa)
- **log.md** — registro cronologico delle operazioni

## Workflow memoria
1. **Prima di rispondere su argomenti personali**: chiama `memory_index()` per vedere cosa esiste, poi `memory_read()` sulle note rilevanti.
2. **Durante la conversazione**: se apprendi qualcosa di nuovo e importante, salvalo con `memory_write()` o `memory_append()`.
3. **A fine conversazione significativa**: salva un riassunto con `memory_append(title="<YYYY-MM-DD>", folder="Conversazioni")`.
4. **Se l'utente vuole acquisire un documento/articolo**: usa `memory_ingest()` per salvarlo in Fonti/, poi elabora i concetti chiave in Memoria/.
5. **Se richiesto un health-check della vault**: usa `memory_lint()`.

## Fatti permanenti vs diario
- **Memoria/** = fatti che non cambiano spesso (chi è X, cosa preferisce l'utente, decisioni prese)
- **Conversazioni/** = cosa è successo oggi, diary-style, append-only
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

        if not msg.get("tool_calls"):
            return msg.get("content") or ""

        messages.append(msg)

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


def stream_run(user_message: str, history: list[dict] | None = None):
    """Generator yielding SSE event dicts: {event, data}.

    Events:
      status  {"phase": "thinking"|"responding"}
      tool    {"name": "<tool_name>"}
      token   {"text": "<chunk>"}
      done    {"reply": "<full_reply>"}
      error   {"message": "<msg>"}
    """
    import re as _re

    messages: list[dict] = [{"role": "system", "content": _SYSTEM}]
    if history:
        messages.extend(history)
    else:
        messages.extend(store.get_history(n=10))
    messages.append({"role": "user", "content": user_message})

    for _ in range(MAX_ITER):
        yield {"event": "status", "data": {"phase": "thinking"}}
        try:
            msg = llm.call(messages, tools=tools.TOOLS)
        except Exception as e:
            yield {"event": "error", "data": {"message": str(e)}}
            yield {"event": "done", "data": {"reply": ""}}
            return

        if not msg.get("tool_calls"):
            content = msg.get("content") or ""
            yield {"event": "status", "data": {"phase": "responding"}}
            for chunk in _re.split(r"(\s+)", content):
                if chunk:
                    yield {"event": "token", "data": {"text": chunk}}
            yield {"event": "done", "data": {"reply": content}}
            return

        messages.append(msg)
        for tc in msg["tool_calls"]:
            fn = tc["function"]
            name = fn["name"]
            args = json.loads(fn.get("arguments") or "{}")
            yield {"event": "tool", "data": {"name": name}}
            result = tools.execute(name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    yield {"event": "done", "data": {"reply": "Raggiunto il limite di iterazioni."}}
