import requests
import csv
import time
import re
from urllib.parse import urlparse

INPUT_FILE = 'domains.txt'
OUTPUT_FILE = 'final_site_status.csv'
TIMEOUT = 10
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (BoatsCheckerBot/1.0)'
}

# Known signatures for Boats Group
BOATSGROUP_SIGNATURES = [
    'boatsgroup.com',
    'dealer spike',
    'dealer-spike',
    'app.boatwizard.com',
    'yachtcloser.com',
    'powered by boats group',
    'boatwizard',
    'marinegroupec',
    'ycwebservice',
    'boats-dns-test.com'
]

def normalize(domain):
    return domain.strip().lower().replace("http://", "").replace("https://", "").strip("/")

def try_variants(domain):
    schemes = ["https", "http"]
    prefixes = ["", "www."]
    variants = []

    for scheme in schemes:
        for prefix in prefixes:
            variants.append(f"{scheme}://{prefix}{domain}")

    return variants

def check_domain(domain):
    domain = normalize(domain)
    tried_urls = try_variants(domain)

    for url in tried_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)

            if 200 <= resp.status_code < 400:
                html = resp.text.lower()
                matched = any(sig in html for sig in BOATSGROUP_SIGNATURES)
                return {
                    "domain": domain,
                    "tried_url": url,
                    "final_url": resp.url,
                    "status_code": resp.status_code,
                    "alive": True,
                    "powered_by_boatsgroup": matched,
                    "status_label": (
                        "alive-boatsgroup" if matched else "alive-not-boatsgroup"
                    ),
                    "error": ""
                }

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            continue

    # All attempts failed
    return {
        "domain": domain,
        "tried_url": "all attempts failed",
        "final_url": "",
        "status_code": "N/A",
        "alive": False,
        "powered_by_boatsgroup": False,
        "status_label": "dead",
        "error": last_error if 'last_error' in locals() else "No valid response"
    }

def main():
    seen = set()
    results = []

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        domains = [normalize(line) for line in f if line.strip()]

    for domain in sorted(set(domains)):
        if domain in seen:
            continue
        seen.add(domain)

        print(f"Checking: {domain}")
        result = check_domain(domain)
        print(f"{domain:<35} → {result['status_label']}")

        results.append(result)

    # Save to CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "domain", "tried_url", "final_url", "status_code",
            "alive", "powered_by_boatsgroup", "status_label", "error"
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Done. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
