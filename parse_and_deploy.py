"""
parse_and_deploy.py — Orchestrator for the Austin events pipeline

Flow:
  1. Scrape all sources  → scrape_abr.fetch_all_sources()
  2. Classify events     → keyword-based, no external API
  3. Write data file     → austin-events-data.json + public/ copy
  4. Deploy to Vercel    → npx vercel --prod

Usage:
  python3 parse_and_deploy.py              # full run, current week
  python3 parse_and_deploy.py --no-deploy  # skip Vercel (testing)
"""

import os
import re
import sys
import json
import subprocess
from datetime import datetime, timedelta

from scrape_abr import fetch_all_sources

DATA_FILE   = os.path.expanduser("~/Sites/austin-events/austin-events-data.json")
PUBLIC_FILE = os.path.expanduser("~/Sites/austin-events/public/austin-events-data.json")


# ─────────────────────────────────────────────
# Keyword-based classification (no API needed)
# ─────────────────────────────────────────────

AI_KEYWORDS = {
    "ai", "a.i.", "artificial intelligence", "machine learning", "ml ",
    "llm", "large language", "gpt", "chatgpt", "openai", "anthropic", "claude",
    "gemini", "llama", "mistral", "deep learning", "neural network",
    "nlp", "natural language", "computer vision", "data science",
    "generative", "genai", "rag ", "vector db", "embedding",
    "robotics", "autonomous", "intelligent automation", "ai agent",
    "langchain", "hugging face", "diffusion", "stable diffusion",
    "prompt engineer", "fine-tun",
}

TECH_KEYWORDS = {
    "tech", "technology", "software", "developer", "coding", "programming",
    "python", "javascript", "typescript", "golang", "rust", "react", "node",
    "startup", "saas", "founder", "entrepreneur", "venture", "investor",
    "product", "ux", "design sprint", "hackathon", "demo day",
    "cloud", "aws", "azure", "devops", "kubernetes", "blockchain",
    "ar/vr", "arvr", "augmented reality", "virtual reality", "medtech",
    "biotech", "fintech", "cybersecurity", "security", "open source",
    "networking", "meetup", "meet up", "workshop", "bootcamp",
    "conference", "summit", "symposium", "panel", "pitch",
}

# Titles that are newsletter CTAs, not events
_JUNK_RE = re.compile(
    r'(?i)^(email(\s+me)?(\s+here)?|register(\s+here)?|sign\s+up|rsvp|'
    r'click\s+here|learn\s+more|read\s+more|view\s+(all|more)|'
    r'subscribe|get\s+tickets|buy\s+tickets|apply\s+now|join\s+us|'
    r'more\s+info(rmation)?|find\s+out\s+more|https?://)'
    r'|\bis\s+an?\s+upcoming\b'
)

_MONTH_PREFIX_RE = re.compile(
    r'^(?:January|February|March|April|May|June|July|August|'
    r'September|October|November|December)\s+\d+:\s*'
)


_WORD_BOUNDARY_CACHE: dict = {}

def _matches(name: str, keywords: set) -> bool:
    """
    Keyword match with word-boundary protection for short terms.
    "ai" must not match "contain", "ux" must not match "linux", etc.
    """
    lower = name.lower()
    for kw in keywords:
        k = kw.rstrip()  # strip trailing space used as a word-separator hint
        if not k:
            continue
        if len(k) <= 3 or kw.endswith(' '):
            # Short keywords need \b so "ai" doesn't match "contain"
            pat = _WORD_BOUNDARY_CACHE.get(k)
            if pat is None:
                pat = re.compile(r'\b' + re.escape(k) + r'\b')
                _WORD_BOUNDARY_CACHE[k] = pat
            if pat.search(lower):
                return True
        else:
            if k in lower:
                return True
    return False


def _clean_title(title: str) -> str:
    """Strip 'May 3: ' date prefixes that ABR embeds in link text."""
    return _MONTH_PREFIX_RE.sub("", title).strip().rstrip(":").strip()


def _clean_time(time_str: str) -> str:
    """Normalize '7:15 PM8:30 PM' → '7:15–8:30 PM'."""
    if not time_str:
        return ""
    normalized = time_str.replace(" ", " ")
    times = re.findall(r"\d{1,2}:\d{2}\s*(?:AM|PM)", normalized, re.IGNORECASE)
    if len(times) >= 2:
        p0 = re.search(r"AM|PM", times[0], re.I).group().upper()
        p1 = re.search(r"AM|PM", times[1], re.I).group().upper()
        start_base = re.sub(r"\s*(?:AM|PM)", "", times[0], flags=re.I).strip()
        end_full   = re.sub(r"\s*(AM|PM)", lambda m: f" {m.group(1).upper()}", times[1], flags=re.I).strip()
        if p0 == p1:
            return f"{start_base}–{end_full}"
        return f"{times[0].strip()}–{end_full}"
    return normalized.strip()


def _auto_tags(title: str, category: str) -> list:
    lower = title.lower()
    tags = []

    if category == "ai":
        tags.append("AI")

    if any(kw in lower for kw in ("hackathon", "buildathon")):
        tags.append("Hackathon")
    elif any(kw in lower for kw in ("workshop", "hands-on", "bootcamp", "training")):
        tags.append("Workshop")
    elif any(kw in lower for kw in ("panel", "debate", "discussion", "fireside", "seminar")):
        tags.append("Panel")
    elif any(kw in lower for kw in ("networking", "mixer", "social", "happy hour",
                                     "meet up", "meetup", "breakfast", "coffee")):
        tags.append("Networking")
    elif any(kw in lower for kw in ("startup", "founder", "pitch", "venture",
                                     "demo day", "accelerator", "investor")):
        tags.append("Startup")
    elif category != "ai":
        tags.append("Tech")

    if category == "ai":
        if any(kw in lower for kw in ("llm", "large language", "gpt", "chatgpt",
                                       "claude", "gemini", "llama")):
            tags.append("LLM")
        if any(kw in lower for kw in ("agent", "agentic", "multi-agent")):
            tags.append("Agents")

    return tags


_MONTH_MAP = {
    m.lower(): i + 1 for i, m in enumerate([
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ])
}


def _parse_event_date(date_str: str, ref_year: int):
    """
    Extract a date from strings like 'May 4', 'May 4, 2026', 'Monday, May 4, 2026 6:00 PM'.
    Returns a datetime.date or None if unparseable.
    """
    if not date_str:
        return None
    m = re.search(
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+(\d{1,2})",
        date_str, re.IGNORECASE,
    )
    if not m:
        return None
    month = _MONTH_MAP[m.group(1).lower()]
    day = int(m.group(2))
    yr = re.search(r"\b(20\d{2})\b", date_str)
    year = int(yr.group(1)) if yr else ref_year
    try:
        from datetime import date as _date
        return _date(year, month, day)
    except ValueError:
        return None


def classify_events(raw_events: list, start_date: datetime, end_date: datetime) -> dict:
    """
    Split events into aiEvents and otherEvents using keyword matching.
    Requires a parseable date within [start_date, end_date]; drops everything else.
    """
    ai_events    = []
    other_events = []
    discarded    = 0

    for e in raw_events:
        raw_name = e.get("name", "")
        title = _clean_title(raw_name)

        # Drop newsletter CTAs and other non-event text
        if not title or len(title) < 10 or _JUNK_RE.search(title):
            discarded += 1
            continue

        # Require a date we can parse and that falls inside the upcoming week
        event_date = _parse_event_date(e.get("date", ""), start_date.year)
        if event_date is None:
            discarded += 1
            continue
        if event_date < start_date.date() or event_date > end_date.date():
            discarded += 1
            continue

        out = {
            "title":       title,
            "date":        e.get("date", ""),
            "time":        _clean_time(e.get("time", "")),
            "location":    e.get("location", ""),
            "description": e.get("description", ""),
            "url":         e.get("url", ""),
            "source":      e.get("source", ""),
            "tags":        [],
        }

        if _matches(raw_name, AI_KEYWORDS):
            out["category"] = "ai"
            out["tags"] = _auto_tags(title, "ai")
            ai_events.append(out)
        elif _matches(raw_name, TECH_KEYWORDS):
            out["category"] = "other"
            out["tags"] = _auto_tags(title, "other")
            other_events.append(out)
        else:
            discarded += 1

    # Sort both lists by date so cards appear in chronological order
    def sort_key(ev):
        d = _parse_event_date(ev["date"], start_date.year)
        return d or start_date.date()

    ai_events.sort(key=sort_key)
    other_events.sort(key=sort_key)

    print(f"[Classify] {len(ai_events)} AI events, {len(other_events)} other events "
          f"(discarded {discarded})")
    return {"aiEvents": ai_events, "otherEvents": other_events}


# ─────────────────────────────────────────────
# Data file helpers
# ─────────────────────────────────────────────

def build_data(classified: dict, start_date: datetime, end_date: datetime, sources: list) -> dict:
    week_label = f"{start_date.strftime('%B %-d')}–{end_date.strftime('%-d, %Y')}"
    return {
        "weekOf":      week_label,
        "startDate":   start_date.strftime("%Y-%m-%d"),
        "endDate":     end_date.strftime("%Y-%m-%d"),
        "generatedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources":     sources,
        "aiEvents":    classified["aiEvents"],
        "otherEvents": classified["otherEvents"],
    }

def write_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[Data] Wrote {DATA_FILE}")

    pub_dir = os.path.dirname(PUBLIC_FILE)
    if os.path.isdir(pub_dir):
        with open(PUBLIC_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Data] Wrote {PUBLIC_FILE}")


# ─────────────────────────────────────────────
# Deploy
# ─────────────────────────────────────────────

def deploy():
    print("[Vercel] Deploying to production...")
    subprocess.run(
        ["npx", "vercel", "--prod", "--yes"],
        cwd=os.path.expanduser("~/Sites/austin-events/"),
        check=True,
    )
    print("[Vercel] Done.")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    no_deploy = "--no-deploy" in sys.argv

    today      = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today                          # start from today
    end_date   = today + timedelta(days=13)     # two full weeks out

    raw_events = fetch_all_sources(start_date, end_date)
    if not raw_events:
        print("[Main] No events found. Aborting.")
        sys.exit(1)

    classified = classify_events(raw_events, start_date, end_date)
    source_names = sorted({e.get("source", "") for e in raw_events if e.get("source")})
    data = build_data(classified, start_date, end_date, source_names)
    write_data(data)

    total = len(data["aiEvents"]) + len(data["otherEvents"])
    print(f"\n✓ {len(data['aiEvents'])} AI  +  {len(data['otherEvents'])} other  =  {total} total events")

    if no_deploy:
        print("[Deploy] Skipped (--no-deploy)")
    else:
        deploy()


if __name__ == "__main__":
    main()
