"""Cron trigger — uv run jarvis-cron
Runs the email digest task on a schedule, plus the Telegram bot for approvals.
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

_CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", "15"))


def email_digest_job():
    log.info("Running email digest job...")
    try:
        reply = run("Controlla le email non lette, fai un triage e per quelle che richiedono risposta prepara una bozza.")
        store.append_message("assistant", reply)
        send(f"📬 *Digest email*\n\n{reply}")
    except Exception as e:
        log.error(f"Email digest failed: {e}")


def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(email_digest_job, "interval", minutes=_CHECK_INTERVAL_MIN, id="email_digest")
    scheduler.start()
    log.info(f"Scheduler started — email digest ogni {_CHECK_INTERVAL_MIN} minuti")

    # Run Telegram bot (blocking — handles approvals and incoming messages)
    log.info("Starting Telegram bot...")
    run_bot()
