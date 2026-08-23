import os
import json
import time
import logging
from .downloader import download_feed
from .parser import parse_lines
from . import cache

logger = logging.getLogger(__name__)

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
    meta_path = cache.get_data_file_path('metadata.json')
    try:
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
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
    """Download, parse, and replace files safely inside RUNTIME_DATA_DIR."""
    runtime_dir = cache.RUNTIME_DATA_DIR
    os.makedirs(runtime_dir, exist_ok=True)

    metadata_file = os.path.join(runtime_dir, 'metadata.json')
    stats_file = os.path.join(runtime_dir, 'statistics.json')

    stats = {
        "feeds": 0,
        "domains": 0,
        "urls": 0,
        "duplicates_removed": 0
    }
    
    success_any = False
    
    for name, feed in FEEDS.items():
        tmp_file = os.path.join(runtime_dir, f"{feed['target']}.tmp")
        target_file = os.path.join(runtime_dir, feed['target'])
        
        if download_feed(feed['url'], tmp_file):
            items = parse_lines(tmp_file)
            if not items:
                logger.warning(f"Feed {name} parsed empty, skipping replacement.")
                if os.path.exists(tmp_file):
                    try:
                        os.remove(tmp_file)
                    except OSError:
                        pass
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
            if os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                except OSError:
                    pass

    if success_any:
        meta = {
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "last_updated_ts": time.time(),
            "version": "1.0",
            "sources": list(FEEDS.keys())
        }
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=4)
            
        stats["last_update"] = meta["last_updated"]
        stats["version"] = "1.0"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4)
            
        return True
        
    return False
