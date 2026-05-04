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

def _matches(name: str, keywords: set) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in keywords)

def classify_events(raw_events: list) -> dict:
    """
    Split events into aiEvents and otherEvents using keyword matching.
    Events matching neither bucket are discarded (pure entertainment, etc.).
    """
    ai_events    = []
    other_events = []

    for e in raw_events:
        name = e.get("name", "")

        # Normalise to the output schema
        out = {
            "title":       name,
            "date":        e.get("date", ""),
            "time":        e.get("time", ""),
            "location":    e.get("location", ""),
            "description": "",
            "url":         e.get("url", ""),
            "source":      e.get("source", ""),
            "tags":        [],
        }

        if _matches(name, AI_KEYWORDS):
            out["category"] = "ai"
            ai_events.append(out)
        elif _matches(name, TECH_KEYWORDS):
            out["category"] = "other"
            other_events.append(out)
        # else: discard (music, bars, etc.)

    print(f"[Classify] {len(ai_events)} AI events, {len(other_events)} other events "
          f"(discarded {len(raw_events) - len(ai_events) - len(other_events)})")
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

    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date   = start_date + timedelta(days=7)

    raw_events = fetch_all_sources(start_date, end_date)
    if not raw_events:
        print("[Main] No events found. Aborting.")
        sys.exit(1)

    classified = classify_events(raw_events)
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
