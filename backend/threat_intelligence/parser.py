import logging

logger = logging.getLogger(__name__)

def parse_lines(file_path: str) -> set:
    """Read a file, remove comments and empty lines, lowercase, and return a set of items."""
    items = set()
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    items.add(line.lower())
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
    return items
