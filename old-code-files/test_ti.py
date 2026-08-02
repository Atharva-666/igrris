import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.threat_intelligence.engine import check
from backend.threat_intelligence.startup import init_threat_intelligence

print("Initializing TI engine...")
init_threat_intelligence()

# Test normal email
print("\nTesting normal email:")
res = check("Hello", "How are you today?", "friend@example.com", "example.com")
print(res)

# Test Malicious URL
print("\nTesting malicious URL:")
res = check("Invoice", "Please check http://evil.com/invoice", "billing@company.com", "company.com")
print(res)

# We need to manually add something to the cache to test it, since feeds are empty initially
from backend.threat_intelligence import cache
cache.MALICIOUS_URLS.add("http://evil.com/invoice")

print("\nTesting malicious URL after injecting to cache:")
res = check("Invoice", "Please check http://evil.com/invoice", "billing@company.com", "company.com")
print(res)
