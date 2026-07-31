import os
import json
import time
import logging
from .downloader import download_feed
from .parser import parse_lines
from . import cache

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
METADATA_FILE = os.path.join(DATA_DIR, 'metadata.json')
STATS_FILE = os.path.join(DATA_DIR, 'statistics.json')

FEEDS = {
    "URLhaus": {
        "url": "https://urlhaus.abuse.ch/downloads/text_recent/",
        "target": "malicious_urls.txt",
        "type": "urls"
    },
    "OpenPhish": {
        "url": "https://openphish.com/feed.txt",
        "target": "phishing_domains.txt",
        "type": "urls"
    },
    "Disposable": {
        "url": "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/master/disposable_email_blocklist.conf",
        "target": "disposable_domains.txt",
        "type": "domains"
    }
}

def check_and_update():
    """Check metadata age and run update if > 24 hours."""
    last_update = 0
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r') as f:
                meta = json.load(f)
                last_update = meta.get('last_updated_ts', 0)
    except Exception:
        pass

    now = time.time()
    if now - last_update > 86400: # 24 hours
        logger.info("Threat feeds are older than 24 hours. Updating...")
        success = run_update()
        if success:
            cache.reload_cache()
    else:
        logger.info("Threat feeds are up to date.")

def run_update() -> bool:
    """Download, parse, and replace files safely."""
    stats = {
        "feeds": 0,
        "domains": 0,
        "urls": 0,
        "duplicates_removed": 0
    }
    
    success_any = False
    
    for name, feed in FEEDS.items():
        tmp_file = os.path.join(DATA_DIR, f"{feed['target']}.tmp")
        target_file = os.path.join(DATA_DIR, feed['target'])
        
        if download_feed(feed['url'], tmp_file):
            items = parse_lines(tmp_file)
            if not items:
                logger.warning(f"Feed {name} parsed empty, skipping replacement.")
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
                continue
                
            # Safely replace using atomic operation
            with open(tmp_file, 'w', encoding='utf-8') as f:
                for item in sorted(items):
                    f.write(item + '\n')
            
            os.replace(tmp_file, target_file)
            logger.info(f"Updated {target_file} with {len(items)} items from {name}.")
            
            stats["feeds"] += 1
            if feed["type"] == "urls":
                stats["urls"] += len(items)
            else:
                stats["domains"] += len(items)
                
            success_any = True
        else:
            logger.error(f"Failed to update feed {name}. Old data preserved.")

    if success_any:
        meta = {
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "last_updated_ts": time.time(),
            "version": "1.0",
            "sources": list(FEEDS.keys())
        }
        with open(METADATA_FILE, 'w') as f:
            json.dump(meta, f, indent=4)
            
        stats["last_update"] = meta["last_updated"]
        stats["version"] = "1.0"
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=4)
            
        return True
        
    return False
