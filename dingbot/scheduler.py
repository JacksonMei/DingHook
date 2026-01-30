"""Scheduler that extracts facts and pushes messages on a regular interval.

Behavior:
- Every `CHECK_INTERVAL_SECONDS` (default 60s) the scheduler will:
  1) For each user in the memory file, call the agent to extract facts and write them to `facts_file`.
  2) Generate a short push message for the user from those facts and send it (no @).
"""

import time
import logging

# Import APScheduler lazily and handle missing dependency gracefully
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    APSCHEDULER_AVAILABLE = True
except Exception:
    BackgroundScheduler = None  # type: ignore
    APSCHEDULER_AVAILABLE = False

from . import agent, sender, config
from . import memory_file, facts_file

logger = logging.getLogger(__name__)

sched = None


def run_cycle():
    """One cycle: extract facts for all users and push messages."""
    now = int(time.time())
    users = memory_file.list_users()
    if not users:
        logger.debug("Scheduler: no users found in memory file")
        return
    for uid in users:
        try:
            facts = agent.extract_facts_for_user(uid)
            facts_file.set_user_facts(uid, facts)
            text = agent.generate_push_from_facts(uid, facts)
            # push to the group (no @)
            sender.send_text_from_env(text)
            logger.info("Scheduler: pushed message for user %s (facts=%d)", uid, len(facts))
        except Exception:
            logger.exception("Scheduler: failed to process user %s", uid)


def _job_wrapper():
    try:
        run_cycle()
    except Exception:
        logger.exception("Scheduler: unexpected error during run_cycle")


def start():
    global sched
    if sched:
        return
    if not APSCHEDULER_AVAILABLE:
        logger.warning("APScheduler not available; scheduler will not start. Install 'APScheduler' to enable scheduled tasks.")
        return
    sched = BackgroundScheduler()
    sched.add_job(_job_wrapper, "interval", seconds=config.CHECK_INTERVAL_SECONDS, max_instances=1)
    sched.start()
    logger.info("Scheduler started (check interval %s seconds)", config.CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    start()
    try:
        # keep running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        if sched:
            sched.shutdown()