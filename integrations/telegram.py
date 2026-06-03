"""Telegram bot client — send messages and handle approvals."""
import os
import asyncio
import requests
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

import memory.store as store

_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", "0"))


# ── simple one-shot send (sync, works without running bot) ────────────────────

def send(text: str) -> None:
    """Fire-and-forget message to the configured chat."""
    if not _TOKEN or not _CHAT_ID:
        print(f"[Telegram] {text}")
        return
    requests.post(
        f"https://api.telegram.org/bot{_TOKEN}/sendMessage",
        json={"chat_id": _CHAT_ID, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )


def send_approval_request(action_id: str, description: str) -> None:
    """Send an inline-keyboard approval message."""
    if not _TOKEN or not _CHAT_ID:
        print(f"[Approval needed] {description}\n  → approve: /ok {action_id}")
        return
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approva", callback_data=f"approve:{action_id}"),
        InlineKeyboardButton("❌ Salta", callback_data=f"skip:{action_id}"),
    ]])
    requests.post(
        f"https://api.telegram.org/bot{_TOKEN}/sendMessage",
        json={
            "chat_id": _CHAT_ID,
            "text": f"*Azione in attesa di approvazione*\n\n{description}\n\n`id: {action_id}`",
            "parse_mode": "Markdown",
            "reply_markup": keyboard.to_json(),
        },
        timeout=10,
    )


# ── long-running bot (used by triggers/cron.py and triggers/webhook.py) ──────

async def _on_callback(update: Update, _ctx) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data  # "approve:abc123" or "skip:abc123"
    verb, action_id = data.split(":", 1)
    status = "approved" if verb == "approve" else "skipped"
    action = store.resolve_action(action_id, status)

    if action is None:
        await query.edit_message_text("⚠️ Azione non trovata.")
        return

    if status == "approved":
        result = _execute_approved(action)
        await query.edit_message_text(f"✅ Eseguito: {result}")
    else:
        await query.edit_message_text(f"❌ Saltato: {action['description']}")


def _execute_approved(action: dict) -> str:
    """Actually execute an action after Telegram approval."""
    t = action["type"]
    p = action["payload"]
    if t == "send_email":
        from integrations.gmail import send_email
        send_email(p["to"], p["subject"], p["body"])
        return f"Email inviata a {p['to']}"
    if t == "create_event":
        from integrations.calendar import create_event
        create_event(p["title"], p["start"], p["end"],
                     p.get("description", ""), p.get("attendees"))
        return f"Evento creato: {p['title']}"
    if t == "write_file":
        from pathlib import Path
        Path(p["path"]).write_text(p["content"])
        return f"File scritto: {p['path']}"
    if t == "shell_exec":
        import subprocess
        res = subprocess.run(
            p["command"], shell=True, capture_output=True, text=True,
            timeout=p.get("timeout", 30),
        )
        out = (res.stdout + res.stderr)[:500]
        return f"Eseguito (rc={res.returncode}):\n{out}"
    if t == "sheets_write":
        from integrations.gsheets import sheets_write
        r = sheets_write(p["spreadsheet_id"], p["range_"], p["values"])
        return f"Sheets aggiornato: {r.get('updated_cells', '?')} celle in {r.get('updated_range', '?')}"
    if t == "sheets_append":
        from integrations.gsheets import sheets_append
        r = sheets_append(p["spreadsheet_id"], p["range_"], p["values"])
        return f"Sheets: aggiunte {r.get('appended_rows', '?')} righe in {r.get('appended_range', '?')}"
    if t == "tasks_create":
        from integrations.gtasks import tasks_create
        r = tasks_create(p["title"], p.get("tasklist_id", "@default"),
                         p.get("due", ""), p.get("notes", ""))
        return f"Task creato: {r['title']} (id: {r['id']})"
    return f"Azione '{t}' eseguita"


async def _on_message(update: Update, _ctx) -> None:
    """Forward plain text messages to the agent loop and reply."""
    from agent.loop import run
    text = update.message.text
    store.append_message("user", text)
    reply = run(text)
    store.append_message("assistant", reply)
    await update.message.reply_text(reply)


def build_app() -> Application:
    app = Application.builder().token(_TOKEN).build()
    app.add_handler(CallbackQueryHandler(_on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_message))
    return app


def run_bot() -> None:
    """Blocking — runs the Telegram bot (polling)."""
    app = build_app()
    app.run_polling()
