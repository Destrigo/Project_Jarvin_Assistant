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
    scheduler = BackgroundScheduler()
    scheduler.add_job(email_digest_job,     "interval", minutes=_CHECK_INTERVAL_MIN, id="email_digest")
    scheduler.add_job(scheduled_tasks_job,  "interval", minutes=1, id="scheduled_tasks")
    scheduler.start()
    log.info(f"Scheduler started — email digest ogni {_CHECK_INTERVAL_MIN} minuti, task check ogni minuto")

    # Run Telegram bot (blocking — handles approvals and incoming messages)
    log.info("Starting Telegram bot...")
    run_bot()
