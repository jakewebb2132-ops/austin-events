"""
scrape_abr.py — Multi-source Austin events scraper

Sources:
  1. Austin Business Review (austinbusinessreview.com) — curated weekly newsletter
     Strategy: Fetch latest /archive issue, extract 🗓️ event links directly from HTML
     
  2. Austin Forum (austinforum.org/events) — AI & tech panel events
     Strategy: Parse structured HTML — title, date, time, location, View Event URL
     
  3. lu.ma/austin — Community events calendar
     Strategy: Luma returns JS-rendered HTML with no links in static fetch.
     We use their public discover API instead: api.lu.ma/discover/get-paginated-events
     
  4. Meetup — AI & tech meetup groups in Austin
     Strategy: Meetup blocks unauthenticated scrapers (403). We query their
     public Open Events API: api.meetup.com/find/events
     No API key required for basic public event search.
"""

import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# ─────────────────────────────────────────────
# SOURCE 1: Austin Business Review
# ─────────────────────────────────────────────

ABR_ARCHIVE = "https://www.austinbusinessreview.com/archive"
ABR_BASE    = "https://www.austinbusinessreview.com"

def get_abr_latest_url():
    resp = requests.get(ABR_ARCHIVE, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/p/week-of-" in href:
            return ABR_BASE + href if href.startswith("/") else href
    return None

def scrape_abr():
    """
    Returns list of {name, url, date_hint, source} dicts extracted
    directly from the latest ABR newsletter page.
    Links are the REAL event URLs as published by Ethan — never guessed.
    """
    issue_url = get_abr_latest_url()
    if not issue_url:
        print("[ABR] Could not find latest issue.")
        return []

    print(f"[ABR] Fetching: {issue_url}")
    resp = requests.get(issue_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    skip_domains = [
        "austinbusinessreview.com", "beehiiv.com",
        "instagram.com", "linkedin.com", "twitter.com",
        "linkedin.com", "loewylaw.com", "gracejonesofsalado.com"
    ]

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if not text or len(text) < 5:
            continue
        if any(d in href for d in skip_domains):
            continue
        # Check parent element for 🗓️ and date context
        parent_text = ""
        for parent in a.parents:
            t = parent.get_text(strip=True)
            if "🗓️" in t or re.search(r"May\s+\d+", t):
                parent_text = t
                break
        date_match = re.search(r"(May\s+\d+(?:[–\-]\d+)?)", parent_text or a.parent.get_text())
        date_hint = date_match.group(1) if date_match else ""

        if date_hint:  # Only include items with a recognisable date
            events.append({
                "name": text,
                "url": href,
                "date_hint": date_hint,
                "source": "austinbusinessreview.com"
            })

    print(f"[ABR] Found {len(events)} events")
    return events


# ─────────────────────────────────────────────
# SOURCE 2: Austin Forum
# ─────────────────────────────────────────────

AUSTIN_FORUM_EVENTS = "https://www.austinforum.org/events"

def scrape_austin_forum(start_date=None, end_date=None):
    """
    Scrapes upcoming events from austinforum.org/events.
    Filters to events within [start_date, end_date] if provided.
    Returns list of {name, url, date, time, location, source} dicts.
    """
    print("[AustinForum] Fetching events page...")
    resp = requests.get(AUSTIN_FORUM_EVENTS, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    # Events are structured as <a href="/events/SLUG"> containing title,
    # then sibling elements with date/time/location
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not re.match(r"^/events/[a-z]", href) and not re.match(r"^https://www.austinforum.org/events/[a-z]", href):
            continue
        # Skip archive/category links
        if "?category=" in href or href == "/events":
            continue

        full_url = "https://www.austinforum.org" + href if href.startswith("/") else href
        title = a.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        # Walk the parent to extract date, time, location from sibling li elements
        parent = a.find_parent(["article", "div", "section"])
        date_str = time_str = location_str = ""
        if parent:
            items = parent.find_all("li")
            for i, li in enumerate(items):
                t = li.get_text(strip=True)
                # Date: e.g. "Tuesday, May 5, 2026"
                if re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b", t) and re.search(r"\d{4}", t):
                    date_str = t
                # Time: e.g. "6:15 PM" "7:45 PM"
                elif re.search(r"\d+:\d+\s*(AM|PM)", t):
                    time_str = t if not time_str else time_str + "–" + t
                # Location: remaining li
                elif t and not t.startswith("http") and len(t) > 3 and not time_str.endswith(t):
                    location_str = t

        # Date filter
        if start_date and date_str:
            try:
                event_dt = datetime.strptime(re.sub(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*", "", date_str).strip(), "%B %d, %Y")
                if event_dt < start_date or event_dt > end_date:
                    continue
            except Exception:
                pass  # include if we can't parse

        events.append({
            "name": title,
            "url": full_url,
            "date": date_str,
            "time": time_str,
            "location": location_str,
            "source": "austinforum.org"
        })

    # Deduplicate by URL
    seen = set()
    unique = []
    for e in events:
        if e["url"] not in seen:
            seen.add(e["url"])
            unique.append(e)

    print(f"[AustinForum] Found {len(unique)} events")
    return unique


# ─────────────────────────────────────────────
# SOURCE 3: Luma Austin (via public API)
# ─────────────────────────────────────────────

LUMA_API = "https://api.lu.ma/discover/get-paginated-events"

def scrape_luma_austin(start_date=None, end_date=None):
    """
    Queries Luma's public discover API for Austin events.
    No auth required. Filters by date window and returns
    {name, url, date, time, location, source} dicts.
    """
    print("[Luma] Querying public API for Austin events...")
    params = {
        "pagination_limit": 50,
        "geo_latitude": 30.2672,
        "geo_longitude": -97.7431,
        "geo_radius_km": 30,
        "period": "future",
    }

    try:
        resp = requests.get(LUMA_API, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Luma] API error: {e}")
        return []

    events = []
    entries = data.get("entries", []) or data.get("events", []) or []

    for entry in entries:
        event = entry.get("event", entry)
        name = event.get("name", "")
        slug = event.get("url") or event.get("slug", "")
        start_at = event.get("start_at", "")
        geo = event.get("geo_address_info", {}) or {}
        location = geo.get("full_address", "") or event.get("location", "")
        url = f"https://lu.ma/{slug}" if slug and not slug.startswith("http") else slug

        if not name or not url:
            continue

        # Date filter
        if start_date and start_at:
            try:
                event_dt = datetime.fromisoformat(start_at.replace("Z", "+00:00")).replace(tzinfo=None)
                if event_dt.date() < start_date.date() or event_dt.date() > end_date.date():
                    continue
            except Exception:
                pass

        date_fmt = ""
        time_fmt = ""
        if start_at:
            try:
                dt = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                date_fmt = dt.strftime("%B %-d")
                time_fmt = dt.strftime("%-I:%M %p")
            except Exception:
                pass

        events.append({
            "name": name,
            "url": url,
            "date": date_fmt,
            "time": time_fmt,
            "location": location,
            "source": "lu.ma/austin"
        })

    print(f"[Luma] Found {len(events)} events")
    return events


# ─────────────────────────────────────────────
# SOURCE 4: Meetup (public Open Events API)
# ─────────────────────────────────────────────

MEETUP_API = "https://api.meetup.com/find/events"

def scrape_meetup_austin(start_date=None, end_date=None):
    """
    Queries Meetup's public find/events API for AI & tech events near Austin.
    No API key required for unauthenticated public search.
    Returns {name, url, date, time, location, source} dicts.
    """
    print("[Meetup] Querying API for Austin AI/tech events...")
    params = {
        "lat": 30.2672,
        "lon": -97.7431,
        "radius": 20,
        "text": "AI tech artificial intelligence",
        "fields": "event_url,venue,local_date,local_time",
        "page": 30,
    }

    try:
        resp = requests.get(MEETUP_API, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Meetup] API error: {e}")
        return []

    events = []
    for item in data:
        name = item.get("name", "")
        url = item.get("link") or item.get("event_url", "")
        local_date = item.get("local_date", "")
        local_time = item.get("local_time", "")
        venue = item.get("venue", {}) or {}
        location = venue.get("name", "") + (f", {venue.get('city', '')}" if venue.get("city") else "")

        if not name or not url:
            continue

        # Date filter
        if start_date and local_date:
            try:
                event_dt = datetime.strptime(local_date, "%Y-%m-%d")
                if event_dt < start_date or event_dt > end_date:
                    continue
            except Exception:
                pass

        date_fmt = ""
        if local_date:
            try:
                date_fmt = datetime.strptime(local_date, "%Y-%m-%d").strftime("%B %-d")
            except Exception:
                date_fmt = local_date

        events.append({
            "name": name,
            "url": url,
            "date": date_fmt,
            "time": local_time,
            "location": location,
            "source": "meetup.com"
        })

    print(f"[Meetup] Found {len(events)} events")
    return events


# ─────────────────────────────────────────────
# Combined runner
# ─────────────────────────────────────────────

def fetch_all_sources(start_date=None, end_date=None):
    """
    Run all four scrapers and return a merged list.
    Caller (parse_and_deploy.py) passes this to Gemini
    for classification into aiEvents / otherEvents.
    """
    results = []
    results.extend(scrape_abr())
    results.extend(scrape_austin_forum(start_date, end_date))
    results.extend(scrape_luma_austin(start_date, end_date))
    results.extend(scrape_meetup_austin(start_date, end_date))
    print(f"\n[Total] {len(results)} raw events across all sources")
    return results

def fetch_latest_newsletter():
    """Legacy shim — parse_and_deploy.py calls this for the ABR-only fallback."""
    url = get_abr_latest_url()
    if not url:
        return None
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


if __name__ == "__main__":
    # Test all scrapers
    start = datetime(2026, 5, 4)
    end   = datetime(2026, 5, 10)
    events = fetch_all_sources(start, end)
    print(f"\n{'─'*70}")
    for e in events:
        print(f"[{e.get('source','?'):25}] {e.get('date','?'):8} | {e.get('name','?')[:45]:45} | {e.get('url','?')[:50]}")
