import threading
import time
import logging
from . import cache
from . import updater

logger = logging.getLogger(__name__)

_update_thread = None

def _run_updater_loop():
    logger.info("Threat Intelligence background updater thread started.")
    while True:
        try:
            updater.check_and_update()
        except Exception as e:
            logger.error(f"Error in Threat Intelligence updater loop: {e}")
        time.sleep(3600)  # Check every hour

def init_threat_intelligence():
    """Load the cache and start the background thread. Call from FastAPI startup."""
    global _update_thread
    logger.info("Initializing Threat Intelligence engine...")
    
    # 1. Load threat cache (if empty, TI will return matched=False and ML runs normally)
    cache.reload_cache()
    
    # 2. Start lightweight background thread
    if _update_thread is None or not _update_thread.is_alive():
        _update_thread = threading.Thread(target=_run_updater_loop, daemon=True)
        _update_thread.start()
