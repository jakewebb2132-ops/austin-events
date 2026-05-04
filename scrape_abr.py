"""
scrape_abr.py — Multi-source Austin AI & tech events scraper

Sources:
  1. Austin Business Review   — weekly newsletter, curated event links
  2. Austin Forum             — austinforum.org/events, AI & tech panels
  3. Luma Austin              — lu.ma public geo-discovery API
  4. Do512                    — per-day pages, keyword-filtered to tech/business only
  5. Capital Factory          — capitalfactory.com/in-person/, static HTML
  6. Eventbrite AI Austin     — eventbrite.com AI category, static HTML
  7. Meetup RSS               — known Austin AI group feeds (no auth required)
"""

import re
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
)
MONTH_RE = "|".join(MONTH_NAMES)


# ─────────────────────────────────────────────
# SOURCE 1: Austin Business Review
# ─────────────────────────────────────────────

ABR_ARCHIVE = "https://www.austinbusinessreview.com/archive"
ABR_BASE    = "https://www.austinbusinessreview.com"

ABR_SKIP_DOMAINS = {
    "austinbusinessreview.com", "beehiiv.com", "instagram.com",
    "linkedin.com", "twitter.com", "loewylaw.com", "gracejonesofsalado.com",
}

def scrape_abr():
    resp = requests.get(ABR_ARCHIVE, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    issue_url = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/p/week-of-" in href:
            issue_url = ABR_BASE + href if href.startswith("/") else href
            break

    if not issue_url:
        print("[ABR] Could not find latest issue.")
        return []

    print(f"[ABR] Fetching: {issue_url}")
    resp = requests.get(issue_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if not text or len(text) < 5:
            continue
        if any(d in href for d in ABR_SKIP_DOMAINS):
            continue
        parent_text = ""
        for parent in a.parents:
            t = parent.get_text(strip=True)
            if "🗓️" in t or re.search(rf"({MONTH_RE})\s+\d+", t):
                parent_text = t
                break
        date_match = re.search(
            rf"((?:{MONTH_RE})\s+\d+(?:[–\-]\d+)?)",
            parent_text or a.parent.get_text()
        )
        if date_match:
            events.append({
                "name": text,
                "url": href,
                "date": date_match.group(1),
                "time": "",
                "location": "",
                "source": "austinbusinessreview.com",
            })

    print(f"[ABR] Found {len(events)} events")
    return events


# ─────────────────────────────────────────────
# SOURCE 2: Austin Forum
# ─────────────────────────────────────────────

def scrape_austin_forum(start_date=None, end_date=None):
    print("[AustinForum] Fetching events page...")
    resp = requests.get("https://www.austinforum.org/events", headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    event_href_re = re.compile(r"^(/events/[a-z]|https://www\.austinforum\.org/events/[a-z])")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not event_href_re.match(href):
            continue
        if "?category=" in href or href == "/events":
            continue

        full_url = "https://www.austinforum.org" + href if href.startswith("/") else href
        title = a.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        parent = a.find_parent(["article", "div", "section"])
        date_str = time_str = location_str = ""
        if parent:
            for li in parent.find_all("li"):
                t = li.get_text(strip=True)
                if re.search(rf"\b({MONTH_RE})\b", t) and re.search(r"\d{{4}}", t):
                    date_str = t
                elif re.search(r"\d+:\d+\s*(AM|PM)", t):
                    time_str = t if not time_str else f"{time_str}–{t}"
                elif t and not t.startswith("http") and len(t) > 3:
                    location_str = t

        if start_date and date_str:
            try:
                clean = re.sub(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*", "", date_str).strip()
                event_dt = datetime.strptime(clean, "%B %d, %Y")
                if event_dt < start_date or event_dt > end_date:
                    continue
            except Exception:
                pass

        events.append({
            "name": title,
            "url": full_url,
            "date": date_str,
            "time": time_str,
            "location": location_str,
            "source": "austinforum.org",
        })

    seen = set()
    unique = [e for e in events if not (e["url"] in seen or seen.add(e["url"]))]
    print(f"[AustinForum] Found {len(unique)} events")
    return unique


# ─────────────────────────────────────────────
# SOURCE 3: Luma Austin (public API)
# ─────────────────────────────────────────────

def scrape_luma_austin(start_date=None, end_date=None):
    print("[Luma] Querying public API...")
    params = {
        "pagination_limit": 50,
        "geo_latitude": 30.2672,
        "geo_longitude": -97.7431,
        "geo_radius_km": 30,
        "period": "future",
    }
    try:
        resp = requests.get(
            "https://api.lu.ma/discover/get-paginated-events",
            params=params, headers=HEADERS, timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[Luma] API error: {e}")
        return []

    events = []
    for entry in data.get("entries", []):
        ev = entry.get("event", entry)
        name = ev.get("name", "")
        slug = ev.get("url") or ev.get("slug", "")
        start_at = ev.get("start_at", "")
        location = (ev.get("geo_address_info") or {}).get("full_address", "") or ev.get("location", "")
        url = f"https://lu.ma/{slug}" if slug and not slug.startswith("http") else slug

        if not name or not url:
            continue
        if start_date and start_at:
            try:
                dt = datetime.fromisoformat(start_at.replace("Z", "+00:00")).replace(tzinfo=None)
                if dt.date() < start_date.date() or dt.date() > end_date.date():
                    continue
            except Exception:
                pass

        date_fmt = time_fmt = ""
        if start_at:
            try:
                dt = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                date_fmt = dt.strftime("%B %-d")
                time_fmt = dt.strftime("%-I:%M %p")
            except Exception:
                pass

        events.append({
            "name": name, "url": url, "date": date_fmt,
            "time": time_fmt, "location": location, "source": "lu.ma/austin",
        })

    print(f"[Luma] Found {len(events)} events")
    return events


# ─────────────────────────────────────────────
# SOURCE 4: Do512 (keyword-filtered)
# ─────────────────────────────────────────────

DO512_KEYWORDS = {
    "ai", "artificial intelligence", "machine learning", "llm", "gpt",
    "deep learning", "neural", "robotics", "data science", "nlp", "automation",
    "tech", "technology", "software", "developer", "coding", "code", "programming",
    "python", "javascript", "web dev", "startup", "saas", "product", "ux", "design",
    "networking", "network", "meetup", "meet up", "entrepreneur", "founder",
    "investor", "venture", "pitch", "accelerator", "hackathon",
    "workshop", "class", "bootcamp", "summit", "conference", "symposium",
    "panel", "talk", "lecture", "seminar", "demo day",
    "community", "civic", "nonprofit", "education", "career",
}

def scrape_do512(start_date=None, end_date=None):
    if not start_date:
        start_date = datetime.now()
    if not end_date:
        end_date = start_date + timedelta(days=7)

    print(f"[Do512] Scraping {start_date.date()} → {end_date.date()}...")
    event_re = re.compile(r"/events/\d{4}/\d+/\d+/[\w\-]+$")
    all_events = []
    seen = set()

    current = start_date
    while current <= end_date:
        url = f"https://www.do512.com/events/{current.year}/{current.month}/{current.day}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Do512] {url}: {e}")
            current += timedelta(days=1)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not event_re.search(href):
                continue
            full_url = "https://www.do512.com" + href if href.startswith("/") else href
            if full_url in seen:
                continue
            seen.add(full_url)
            name = re.sub(r"\s+", " ", a.get_text(separator=" ", strip=True))
            if not name or len(name) < 5:
                continue
            lower = name.lower()
            if not any(kw in lower for kw in DO512_KEYWORDS):
                continue
            all_events.append({
                "name": name,
                "url": full_url,
                "date": current.strftime("%B %-d"),
                "time": "",
                "location": "Austin, TX",
                "source": "do512.com",
            })
        current += timedelta(days=1)

    print(f"[Do512] Found {len(all_events)} relevant events")
    return all_events


# ─────────────────────────────────────────────
# SOURCE 5: Capital Factory
# ─────────────────────────────────────────────

CF_BASE = "https://capitalfactory.com"

def scrape_capital_factory(start_date=None, end_date=None):
    print("[CapitalFactory] Fetching in-person events...")
    try:
        resp = requests.get(f"{CF_BASE}/in-person/", headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[CapitalFactory] Error: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []
    seen = set()

    # Events are anchor tags pointing to /event/slug
    event_re = re.compile(r"^(/event/|https://capitalfactory\.com/event/)")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not event_re.match(href):
            continue
        full_url = CF_BASE + href if href.startswith("/") else href
        if full_url in seen:
            continue
        seen.add(full_url)

        # Title: the visible link text, or a heading inside the card
        card = a.find_parent(["article", "div", "li", "section"])
        title = ""
        if card:
            h = card.find(["h2", "h3", "h4"])
            title = h.get_text(strip=True) if h else a.get_text(strip=True)
        if not title:
            title = a.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        # Date and time: look for text matching "May 4 @ 6:00pm" patterns
        date_str = time_str = ""
        if card:
            text = card.get_text(" ", strip=True)
            dm = re.search(rf"({MONTH_RE})\s+(\d+)", text)
            tm = re.search(r"(\d+:\d+\s*(?:am|pm))", text, re.IGNORECASE)
            if dm:
                date_str = f"{dm.group(1)} {dm.group(2)}"
            if tm:
                time_str = tm.group(1)

        # Date filter
        if start_date and date_str:
            try:
                event_dt = datetime.strptime(f"{date_str} {start_date.year}", "%B %d %Y")
                if event_dt.date() < start_date.date() or event_dt.date() > end_date.date():
                    continue
            except Exception:
                pass

        events.append({
            "name": title,
            "url": full_url,
            "date": date_str,
            "time": time_str,
            "location": "Capital Factory, Austin TX",
            "source": "capitalfactory.com",
        })

    print(f"[CapitalFactory] Found {len(events)} events")
    return events


# ─────────────────────────────────────────────
# SOURCE 6: Eventbrite — Austin AI category
# ─────────────────────────────────────────────

EB_BASE = "https://www.eventbrite.com"

def scrape_eventbrite_ai(start_date=None, end_date=None):
    print("[Eventbrite] Fetching Austin AI events...")
    url = f"{EB_BASE}/d/tx--austin/artificial-intelligence/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Eventbrite] Error: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []
    seen = set()

    # Event links match /e/event-name-tickets-NNNNN
    event_re = re.compile(r"/e/[\w\-]+-tickets-\d+")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not event_re.search(href):
            continue
        # Normalize to absolute URL, strip query params
        full_url = href if href.startswith("http") else EB_BASE + href
        full_url = full_url.split("?")[0]
        if full_url in seen:
            continue
        seen.add(full_url)

        # Walk up to find the event card
        card = a.find_parent(["article", "li", "div"])
        title = a.get_text(strip=True)
        if card and not title:
            h = card.find(["h2", "h3"])
            title = h.get_text(strip=True) if h else ""
        if not title or len(title) < 5:
            continue

        date_str = time_str = ""
        if card:
            text = card.get_text(" ", strip=True)
            dm = re.search(rf"({MONTH_RE})\s+(\d+)", text)
            tm = re.search(r"(\d+:\d+\s*(?:AM|PM|am|pm))", text)
            if dm:
                date_str = f"{dm.group(1)} {dm.group(2)}"
            if tm:
                time_str = tm.group(1)

        if start_date and date_str:
            try:
                event_dt = datetime.strptime(f"{date_str} {start_date.year}", "%B %d %Y")
                if event_dt.date() < start_date.date() or event_dt.date() > end_date.date():
                    continue
            except Exception:
                pass

        events.append({
            "name": title,
            "url": full_url,
            "date": date_str,
            "time": time_str,
            "location": "Austin, TX",
            "source": "eventbrite.com",
        })

    print(f"[Eventbrite] Found {len(events)} events")
    return events


# ─────────────────────────────────────────────
# SOURCE 7: Meetup RSS — known Austin AI groups
# ─────────────────────────────────────────────

# Active groups verified May 2026. Add slugs here as new groups are found.
MEETUP_GROUPS = [
    "ai-austin",           # Austin AI, GenAI and ML — 8k+ members
    "austin-deep-learning", # Austin Deep Learning — active monthly meetups
]

def _parse_rss_date(date_str: str):
    """Parse RSS pubDate like 'Fri, 03 Jan 2026 00:00:00 +0000'."""
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(date_str.strip(), fmt).replace(tzinfo=None)
        except Exception:
            pass
    return None

def scrape_meetup_rss(start_date=None, end_date=None):
    print(f"[Meetup] Fetching RSS for {len(MEETUP_GROUPS)} groups...")
    events = []
    seen = set()

    for slug in MEETUP_GROUPS:
        url = f"https://www.meetup.com/{slug}/events/rss/"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 404:
                print(f"[Meetup] {slug}: 404, skipping")
                continue
            resp.raise_for_status()
        except Exception as e:
            print(f"[Meetup] {slug}: {e}")
            continue

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as e:
            print(f"[Meetup] {slug}: XML parse error: {e}")
            continue

        def _tag(item, name):
            node = item.find(name)
            return (node.text or "").strip() if node is not None else ""

        items = root.findall(".//item")
        for item in items:
            title = _tag(item, "title")
            link  = _tag(item, "link") or _tag(item, "guid")
            pub   = _tag(item, "pubDate")
            desc  = _tag(item, "description")

            if not title or title == "TBD" or not link:
                continue
            if link in seen:
                continue
            seen.add(link)

            event_dt = _parse_rss_date(pub) if pub else None

            if start_date and event_dt:
                if event_dt.date() < start_date.date() or event_dt.date() > end_date.date():
                    continue

            date_str = event_dt.strftime("%B %-d") if event_dt else ""

            # Try to extract time and location from description
            time_str = ""
            location_str = "Austin, TX"
            if desc:
                tm = re.search(r"(\d+:\d+\s*(?:AM|PM|am|pm))", desc)
                if tm:
                    time_str = tm.group(1)
                loc = re.search(r"(?:Location|Venue|Address)[:\s]+([^\n<]{5,60})", desc, re.IGNORECASE)
                if loc:
                    location_str = loc.group(1).strip()

            events.append({
                "name": title,
                "url": link,
                "date": date_str,
                "time": time_str,
                "location": location_str,
                "source": "meetup.com",
            })

        count = sum(1 for e in events if slug in e.get("url", ""))
        print(f"[Meetup] {slug}: {count} events")

    print(f"[Meetup] Total: {len(events)} events")
    return events


# ─────────────────────────────────────────────
# Combined runner
# ─────────────────────────────────────────────

def fetch_all_sources(start_date=None, end_date=None):
    """
    Run all seven scrapers. Each source is isolated — a failure in one
    never kills the others. Returns a merged, URL-deduplicated list.
    """
    scrapers = [
        ("ABR",            lambda: scrape_abr()),
        ("AustinForum",    lambda: scrape_austin_forum(start_date, end_date)),
        ("Luma",           lambda: scrape_luma_austin(start_date, end_date)),
        ("Do512",          lambda: scrape_do512(start_date, end_date)),
        ("CapitalFactory", lambda: scrape_capital_factory(start_date, end_date)),
        ("Eventbrite",     lambda: scrape_eventbrite_ai(start_date, end_date)),
        ("Meetup",         lambda: scrape_meetup_rss(start_date, end_date)),
    ]

    seen_urls = set()
    results = []
    for name, fn in scrapers:
        try:
            for e in fn():
                url = e.get("url", "")
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                results.append(e)
        except Exception as ex:
            print(f"[{name}] FAILED (skipping): {ex}")

    print(f"\n[Total] {len(results)} unique events across all sources")
    return results


if __name__ == "__main__":
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end   = start + timedelta(days=7)
    events = fetch_all_sources(start, end)
    print(f"\n{'─'*70}")
    for e in events:
        print(f"[{e.get('source','?'):25}] {e.get('date','?'):10} | {e.get('name','?')[:45]:45} | {e.get('url','?')[:55]}")
