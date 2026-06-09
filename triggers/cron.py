"""Cron trigger — uv run jarvis-cron

Jobs:
  daily_digest     — ogni mattina alle DAILY_DIGEST_HOUR (default 8), include email di ieri
  followup_check   — ogni giorno alle 9:00, notifica mail senza risposta
  weekly_journal   — ogni domenica alle 20:00, riassunto diario settimanale
  alerts_check     — ogni CHECK_ALERTS_MIN minuti (default 5)
  scheduled_tasks  — ogni minuto
  self_ping        — ogni 10 minuti (Render free tier keepalive)
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

from apscheduler.schedulers.background import BackgroundScheduler
from integrations.telegram import send, run_bot
from agent.loop import run
import memory.store as store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

_CHECK_ALERTS_MIN    = int(os.getenv("CHECK_ALERTS_MIN", "5"))
_DAILY_DIGEST_HOUR   = int(os.getenv("DAILY_DIGEST_HOUR", "8"))
_DAILY_DIGEST_CITY   = os.getenv("DAILY_DIGEST_CITY", "")


def daily_digest_job():
    log.info("Running daily digest job...")
    from datetime import date, timedelta
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y/%m/%d")
    today     = date.today().strftime("%Y/%m/%d")
    try:
        prompt = (
            "Buongiorno! Prepara il digest mattutino con:\n"
            "1. Gli eventi di calendario di oggi (list_events con days_ahead=1)\n"
            f"2. Tutte le email ricevute ieri — usa list_emails con query='after:{yesterday} before:{today}' e max_results=50. "
            "Raggruppa per mittente o tema, evidenzia quelle urgenti o che richiedono risposta.\n"
            "3. I task Google in scadenza oggi o già scaduti (tasks_list)\n"
            + (f"4. Il meteo a {_DAILY_DIGEST_CITY} (weather)\n" if _DAILY_DIGEST_CITY else "")
            + "Formatta il tutto in modo conciso e leggibile per Telegram. "
            "Niente prefazioni verbose, vai dritto alle informazioni."
        )
        reply = run(prompt)
        store.append_message("assistant", reply)
        send(f"🌅 *Buongiorno — digest del giorno*\n\n{reply}")
    except Exception as e:
        log.error(f"Daily digest failed: {e}")


def followup_check_job():
    log.info("Running follow-up check job...")
    try:
        from integrations.followups import check
        from datetime import datetime, timezone
        overdue = check()
        for entry in overdue:
            sent_at = datetime.fromisoformat(entry["sent_at"])
            days = int((datetime.now(timezone.utc) - sent_at).total_seconds() / 86400)
            send(
                f"📭 *Nessuna risposta dopo {days} giorni*\n\n"
                f"A: {entry['to']}\n"
                f"Oggetto: {entry['subject']}\n\n"
                f"Vuoi che prepari un follow-up?\n`id: {entry['id']}`"
            )
    except Exception as e:
        log.error(f"Follow-up check failed: {e}")


def weekly_journal_job():
    log.info("Running weekly journal summary job...")
    try:
        from integrations.journal import get_week_entries
        entries = get_week_entries()
        if not entries:
            send("📓 *Riassunto settimanale*\n\nNessun appunto registrato questa settimana.")
            return
        combined = "\n\n".join(f"**{d}**\n{content}" for d, content in entries.items())
        prompt = (
            "Sei il mio assistente personale. Ho registrato questi appunti nel diario questa settimana:\n\n"
            f"{combined}\n\n"
            "Fai un riassunto conciso della settimana: temi ricorrenti, decisioni prese, cose da ricordare. "
            "Tono personale e diretto, senza fronzoli. Massimo 300 parole."
        )
        reply = run(prompt)
        store.append_message("assistant", reply)
        send(f"📓 *Riassunto della settimana*\n\n{reply}")
    except Exception as e:
        log.error(f"Weekly journal failed: {e}")


def alerts_check_job():
    log.info("Running alerts check job...")
    try:
        from integrations.alerts import check_alerts
        triggered = check_alerts()
        for alert in triggered:
            msg = f"🔔 *Alert: {alert['name']}*\n\n{alert['message']}"
            send(msg)
            log.info(f"Alert triggered: {alert['name']}")
    except Exception as e:
        log.error(f"Alerts check failed: {e}")


def self_ping_job():
    """Ping /health every 10 min to prevent Render free tier spin-down."""
    import requests
    url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8080")
    try:
        requests.get(f"{url}/health", timeout=10)
        log.debug(f"Self-ping OK: {url}/health")
    except Exception as e:
        log.warning(f"Self-ping failed: {e}")


def scheduled_tasks_job():
    """Pick up and execute any tasks Jarvis scheduled for itself."""
    from integrations.scheduler import pop_due_tasks, mark_done
    due = pop_due_tasks()
    for task_entry in due:
        task_id = task_entry["id"]
        instruction = task_entry["task"]
        log.info(f"Executing scheduled task {task_id}: {instruction[:60]}...")
        try:
            reply = run(instruction)
            store.append_message("assistant", reply)
            send(f"⏰ *Task schedulato eseguito*\n\n_{instruction[:80]}_\n\n{reply}")
            mark_done(task_id, reply)
        except Exception as e:
            log.error(f"Scheduled task {task_id} failed: {e}")
            mark_done(task_id, f"ERRORE: {e}")


def main():
    import signal, os

    def _force_exit(sig, frame):
        log.info("Secondo segnale — uscita forzata.")
        os._exit(0)

    def _graceful(sig, frame):
        log.info("SIGINT ricevuto — premi di nuovo Ctrl+C per forzare l'uscita.")
        signal.signal(signal.SIGINT, _force_exit)
        signal.signal(signal.SIGTERM, _force_exit)
        os._exit(0)

    signal.signal(signal.SIGINT, _graceful)
    signal.signal(signal.SIGTERM, _graceful)

    scheduler = BackgroundScheduler()
    scheduler.add_job(daily_digest_job,   "cron",     hour=_DAILY_DIGEST_HOUR, minute=0, id="daily_digest")
    scheduler.add_job(followup_check_job, "cron",     hour=9,  minute=0,              id="followup_check")
    scheduler.add_job(weekly_journal_job, "cron",     day_of_week="sun", hour=20, minute=0, id="weekly_journal")
    scheduler.add_job(alerts_check_job,   "interval", minutes=_CHECK_ALERTS_MIN,      id="alerts_check")
    scheduler.add_job(scheduled_tasks_job,"interval", minutes=1,                      id="scheduled_tasks")
    scheduler.add_job(self_ping_job,      "interval", minutes=10,                     id="self_ping")
    scheduler.start()
    log.info(
        f"Scheduler started — digest alle {_DAILY_DIGEST_HOUR}:00, "
        f"follow-up check alle 9:00, "
        f"riassunto diario domenica 20:00, "
        f"alert ogni {_CHECK_ALERTS_MIN}min"
    )

    log.info("Starting Telegram bot...")
    run_bot()
