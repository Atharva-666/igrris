import os
import logging

logger = logging.getLogger(__name__)

SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
RUNTIME_DATA_DIR = os.environ.get(
    'TI_RUNTIME_DIR',
    os.path.join(os.path.dirname(__file__), 'runtime_data')
)

# Use global references for atomic replacement
BLACKLIST_DOMAINS = set()
PHISHING_DOMAINS = set()
MALICIOUS_URLS = set()
MALICIOUS_IPS = set()
DISPOSABLE_DOMAINS = set()
TRUSTED_DOMAINS = set()
SUSPICIOUS_TLDS = set()
URL_SHORTENERS = set()
KEYWORDS = []
USER_BLACKLIST = set()
USER_WHITELIST = set()

def get_data_file_path(filename: str) -> str:
    """
    Return path for a TI data file.
    Prefers RUNTIME_DATA_DIR if file exists there and is non-empty (>0 bytes).
    Otherwise falls back to SEED_DATA_DIR.
    """
    runtime_path = os.path.join(RUNTIME_DATA_DIR, filename)
    if os.path.exists(runtime_path) and os.path.getsize(runtime_path) > 0:
        return runtime_path
    return os.path.join(SEED_DATA_DIR, filename)

def _load_set(filename: str) -> set:
    s = set()
    path = get_data_file_path(filename)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    val = line.strip().lower()
                    if val and not val.startswith('#'):
                        s.add(val)
        except Exception as e:
            logger.error(f"Error loading {filename} from {path}: {e}")
    return s

def _load_json_list(filename: str, key: str) -> list:
    path = get_data_file_path(filename)
    if os.path.exists(path):
        import json
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(key, [])
        except Exception as e:
            logger.error(f"Error loading {filename} from {path}: {e}")
    return []

def reload_cache():
    global BLACKLIST_DOMAINS, PHISHING_DOMAINS, MALICIOUS_URLS, MALICIOUS_IPS
    global DISPOSABLE_DOMAINS, TRUSTED_DOMAINS, SUSPICIOUS_TLDS, URL_SHORTENERS
    global KEYWORDS, USER_BLACKLIST, USER_WHITELIST

    logger.info("Loading threat intelligence cache...")
    
    new_blacklist = _load_set('blacklist_domains.txt')
    new_phishing = _load_set('phishing_domains.txt')
    new_urls = _load_set('malicious_urls.txt')
    new_ips = _load_set('malicious_ips.txt')
    new_disposable = _load_set('disposable_domains.txt')
    new_trusted = _load_set('trusted_domains.txt')
    new_tlds = _load_set('suspicious_tlds.txt')
    new_shorteners = _load_set('url_shorteners.txt')
    
    new_user_bl = _load_set('user_blacklist.txt')
    new_user_wl = _load_set('user_whitelist.txt')
    
    new_keywords = _load_json_list('keywords.json', 'suspicious')

    # Atomic replacements using old -> new references
    BLACKLIST_DOMAINS = new_blacklist
    PHISHING_DOMAINS = new_phishing
    MALICIOUS_URLS = new_urls
    MALICIOUS_IPS = new_ips
    DISPOSABLE_DOMAINS = new_disposable
    TRUSTED_DOMAINS = new_trusted
    SUSPICIOUS_TLDS = new_tlds
    URL_SHORTENERS = new_shorteners
    USER_BLACKLIST = new_user_bl
    USER_WHITELIST = new_user_wl
    KEYWORDS = new_keywords
    
    logger.info("Threat intelligence cache loaded successfully.")
