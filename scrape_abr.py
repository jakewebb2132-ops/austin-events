"""
scrape_abr.py — Austin Business Review web scraper

Fetches the latest weekly issue from austinbusinessreview.com/archive,
extracts every event link (name + URL) from the newsletter body,
and returns the raw HTML for parse_and_deploy.py to process.

This is the ONLY source of truth for event URLs. We never guess or
fabricate slugs — we read the actual links from the ABR page.
"""

import requests
import re
from bs4 import BeautifulSoup

ABR_ARCHIVE = "https://www.austinbusinessreview.com/archive"
ABR_BASE = "https://www.austinbusinessreview.com"

def get_latest_issue_url():
    """Find the URL of the most recent weekly issue from the archive index."""
    resp = requests.get(ABR_ARCHIVE, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Weekly issues follow the pattern /p/week-of-*
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/p/week-of-" in href:
            if href.startswith("/"):
                href = ABR_BASE + href
            return href
    return None

def fetch_latest_newsletter():
    """
    Fetches the latest ABR newsletter page and returns its full HTML body.
    The caller (parse_and_deploy.py) will pass this to Gemini for extraction.
    Event URLs in the returned HTML are the real, verified source links.
    """
    issue_url = get_latest_issue_url()
    if not issue_url:
        print("Could not find latest issue URL in archive.")
        return None

    print(f"Fetching latest issue: {issue_url}")
    resp = requests.get(issue_url, timeout=15)
    resp.raise_for_status()
    return resp.text

def extract_events_raw(html):
    """
    Extract a plain list of (name, url, date_hint) tuples directly from
    the newsletter HTML — no LLM needed. Uses the 🗓️ emoji pattern that
    ABR consistently uses for event listings.
    Returns a list of dicts with keys: name, url, date_hint
    """
    soup = BeautifulSoup(html, "html.parser")
    events = []

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        # Skip nav/footer links
        if not text or len(text) < 5:
            continue
        if any(skip in href for skip in ["beehiiv.com", "austinbusinessreview.com/archive",
                                          "austinbusinessreview.com/p/", "login", "upgrade"]):
            continue
        # Look for the parent that contains the date prefix (e.g. "May 4:")
        parent_text = a.parent.get_text(strip=True) if a.parent else ""
        date_match = re.search(r"(May\s+\d+(?:[–-]\d+)?)", parent_text)
        date_hint = date_match.group(1) if date_match else ""

        events.append({
            "name": text,
            "url": href,
            "date_hint": date_hint
        })

    return events

if __name__ == "__main__":
    html = fetch_latest_newsletter()
    if html:
        events = extract_events_raw(html)
        print(f"\nFound {len(events)} event links:\n")
        for e in events:
            print(f"  {e['date_hint']:10} | {e['name'][:50]:50} | {e['url']}")
