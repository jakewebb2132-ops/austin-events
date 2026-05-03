"""
scrape_abr.py — Multi-source Austin events scraper

Sources:
  1. Austin Business Review (austinbusinessreview.com) — curated weekly newsletter
     Strategy: Fetch latest /archive issue, extract 🗓️ event links directly from HTML

  2. Austin Forum (austinforum.org/events) — AI & tech panel events
     Strategy: Parse structured HTML — title, date, time, location, View Event URL

  3. lu.ma/austin — Community events calendar
     Strategy: Luma's static HTML has no event URLs (JS-rendered).
     We use their public geo-discovery API instead.

  4. Do512 (do512.com) — Austin's best local events aggregator
     Strategy: Scrape per-day pages (do512.com/events/YYYY/M/D) for each day
     in the target week. HTML is fully static and well-structured.
     Covers workshops, classes, community events, and culture.

  NOT included (blocked):
  - Meetup.com — 403 on all endpoints; paid API is $47/mo
  - Eventbrite browse pages — 429 rate-limited + JS-rendered
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
# SOURCE 4: Do512 (Austin local events aggregator)
# ─────────────────────────────────────────────

DO512_BASE = "https://www.do512.com"

# Do512 categories relevant to tech/community events (skip pure music/nightlife)
DO512_CATEGORIES = [
    "workshops-classes",
    "community",
    "art-culture",
    "variety-other",
]

def scrape_do512_day(date: datetime):
    """Scrape a single day's events from Do512."""
    url = f"{DO512_BASE}/events/{date.year}/{date.month}/{date.day}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Do512] Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    # Events are anchor tags matching /events/YYYY/M/D/slug-name
    event_pattern = re.compile(r"/events/\d{4}/\d+/\d+/[\w\-]+$")
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not event_pattern.search(href):
            continue
        full_url = DO512_BASE + href if href.startswith("/") else href
        if full_url in seen:
            continue
        seen.add(full_url)

        name = a.get_text(separator=" ", strip=True)
        # Clean up whitespace and newlines
        name = re.sub(r"\s+", " ", name).strip()
        if not name or len(name) < 5:
            continue
        # Skip obviously non-relevant (pure music gig names are fine —
        # Gemini will classify them as otherEvents or drop them)
        events.append({
            "name": name,
            "url": full_url,
            "date": date.strftime("%B %-d"),
            "time": "",
            "location": "Austin, TX",
            "source": "do512.com"
        })

    return events

def scrape_do512(start_date=None, end_date=None):
    """
    Scrapes Do512 for each day in [start_date, end_date].
    Returns merged list of {name, url, date, time, location, source}.
    """
    if not start_date:
        start_date = datetime.now()
    if not end_date:
        end_date = start_date + timedelta(days=7)

    print(f"[Do512] Scraping {start_date.date()} → {end_date.date()}...")
    all_events = []
    current = start_date
    while current <= end_date:
        day_events = scrape_do512_day(current)
        all_events.extend(day_events)
        current += timedelta(days=1)

    # Deduplicate
    seen = set()
    unique = []
    for e in all_events:
        if e["url"] not in seen:
            seen.add(e["url"])
            unique.append(e)

    print(f"[Do512] Found {len(unique)} events")
    return unique


# ─────────────────────────────────────────────
# Combined runner
# ─────────────────────────────────────────────

def fetch_all_sources(start_date=None, end_date=None):
    """
    Run all four scrapers and return a merged list.
    Caller (parse_and_deploy.py) passes this to Gemini
    for classification into aiEvents / otherEvents.

    Sources: ABR newsletter, Austin Forum, Luma API, Do512
    """
    results = []
    results.extend(scrape_abr())
    results.extend(scrape_austin_forum(start_date, end_date))
    results.extend(scrape_luma_austin(start_date, end_date))
    results.extend(scrape_do512(start_date, end_date))
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
