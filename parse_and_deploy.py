import os
import sys
import json
import subprocess
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/GTM Agents/.env"))
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

DATA_FILE = os.path.expanduser("~/Sites/austin-events/austin-events-data.json")

def extract_events_with_gemini(html_content):
    prompt = """
    Extract all events from this HTML content.
    Return a JSON object matching this exact schema:
    {
      "aiEvents": [
        {"title": "", "date": "May X", "time": "", "location": "", "description": "", "url": "", "source": "", "category": "ai", "tags": []}
      ],
      "otherEvents": [
        {"title": "", "date": "May X", "time": "", "location": "", "description": "", "url": "", "source": "", "category": "other", "tags": []}
      ]
    }
    Ensure all events have a verified URL. Put AI events in aiEvents, and networking/business in otherEvents.
    HTML Content:
    """ + html_content

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    try:
        # Strip markdown formatting if present
        text = response.text.strip()
        if text.startswith('```json'): text = text[7:]
        if text.endswith('```'): text = text[:-3]
        return json.loads(text)
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {"aiEvents": [], "otherEvents": []}

def update_data_file(new_events):
    if not os.path.exists(DATA_FILE):
        return False
        
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        
    # Append new events
    data['aiEvents'].extend(new_events.get('aiEvents', []))
    data['otherEvents'].extend(new_events.get('otherEvents', []))
    data['generatedAt'] = datetime.now().isoformat()
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
        
    # Also copy to public/
    public_file = os.path.expanduser("~/Sites/austin-events/public/austin-events-data.json")
    if os.path.exists(os.path.dirname(public_file)):
        with open(public_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    return len(new_events.get('aiEvents', [])) + len(new_events.get('otherEvents', []))

def deploy_to_vercel():
    print("Deploying to Vercel...")
    subprocess.run(["npx", "vercel", "--prod", "--yes"], cwd=os.path.expanduser("~/Sites/austin-events/"), check=True)
    
def run_from_web():
    from scrape_abr import fetch_latest_newsletter
    print("Running fallback web scraper...")
    html = fetch_latest_newsletter()
    if html:
        process_html(html)
    else:
        print("No content found on web.")

def process_html(html_content):
    print("Extracting events...")
    new_events = extract_events_with_gemini(html_content)
    count = update_data_file(new_events)
    print(f"Added {count} new events.")
    deploy_to_vercel()
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If file is provided
        file_path = sys.argv[1]
        with open(file_path, 'r') as f:
            process_html(f.read())
    else:
        # Fallback to web
        run_from_web()
