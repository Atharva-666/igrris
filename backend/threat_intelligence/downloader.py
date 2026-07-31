import logging
import urllib.request
import os

logger = logging.getLogger(__name__)

def download_feed(url: str, output_path: str) -> bool:
    """Download a threat feed to a temporary file."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Igrris-AI/1.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        logger.info(f"Downloaded {url} to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download feed {url}: {e}")
        return False
