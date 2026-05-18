import requests
from bs4 import BeautifulSoup
import re
import sys
import io
import json
import os
from datetime import datetime, timedelta

# Fix Unicode encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "https://limbuscompany.wiki.gg/wiki/Ry%C5%8Dsh%C5%AB"
CACHE_FILE = "sangria_cache.json"
CACHE_DURATION = timedelta(hours=1)


def fetch_sangria_data():
    """Fetch and parse the SANGRIA table from the wiki page."""
    response = requests.get(URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    table = soup.find("table", class_="wikitable")
    if not table:
        print("Could not find the SANGRIA table.")
        return []

    rows = table.find_all("tr")
    entries = []
    current_section = "General"

    for row in rows:
        cells = row.find_all(["th", "td"])

        # Skip the main header row (SANGRIA, Translation, Reliability, Source)
        if len(cells) == 4 and cells[0].get_text(strip=True) == "SANGRIA" and \
           cells[1].get_text(strip=True) == "Translation":
            continue

        # Check if it's a section header (Canto/Intervallo row) - colspan=4
        if len(cells) == 1 and cells[0].has_attr("colspan"):
            current_section = cells[0].get_text(strip=True)
            continue

        # Data row
        if len(cells) >= 4:
            sangria = cells[0].get_text(strip=True)
            translation = cells[1].get_text(strip=True)
            reliability = cells[2].get_text(strip=True)
            source = cells[3].get_text(strip=True)

            entries.append({
                "section": current_section,
                "sangria": sangria,
                "translation": translation,
                "reliability": reliability,
                "source": source,
            })

    return entries


def save_cache(entries):
    """Save entries to the cache JSON file with a timestamp."""
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "entries": entries,
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)


def load_cache():
    """Load entries from the cache JSON file."""
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache_data = json.load(f)
    return cache_data["entries"], cache_data["timestamp"]


def is_cache_fresh():
    """Check if the cache file exists and is within the freshness duration."""
    if not os.path.exists(CACHE_FILE):
        return False

    try:
        _, timestamp_str = load_cache()
        cache_time = datetime.fromisoformat(timestamp_str)
        return datetime.now() - cache_time < CACHE_DURATION
    except (json.JSONDecodeError, KeyError, ValueError):
        return False


def get_cache_age():
    """Return a human-readable string of how old the cache is."""
    if not os.path.exists(CACHE_FILE):
        return "No cache exists."

    try:
        _, timestamp_str = load_cache()
        cache_time = datetime.fromisoformat(timestamp_str)
        age = datetime.now() - cache_time

        if age < timedelta(minutes=1):
            return "Less than a minute old"
        elif age < timedelta(hours=1):
            minutes = int(age.total_seconds() // 60)
            return f"{minutes} minute(s) old"
        elif age < timedelta(days=1):
            hours = int(age.total_seconds() // 3600)
            minutes = int((age.total_seconds() % 3600) // 60)
            return f"{hours} hour(s), {minutes} minute(s) old"
        else:
            days = age.days
            return f"{days} day(s) old"
    except (json.JSONDecodeError, KeyError, ValueError):
        return "Cache is corrupted."


def load_or_fetch_data(force_refresh=False):
    """
    Load data from cache if fresh, otherwise fetch from the website.
    
    Args:
        force_refresh: If True, always fetch from the website and update cache.
    
    Returns:
        Tuple of (entries list, source string)
    """
    if force_refresh:
        print("  [Force-refreshing from website...]")
        entries = fetch_sangria_data()
        save_cache(entries)
        return entries, "website (cache updated)"

    if is_cache_fresh():
        entries, _ = load_cache()
        return entries, "cache"

    print("  [Cache is stale or missing. Fetching from website...]")
    entries = fetch_sangria_data()
    save_cache(entries)
    return entries, "website (cache saved)"


def display_entries(entries):
    """Display a list of SANGRIA entries in a formatted way."""
    if not entries:
        print("  No matching entries found.")
        return

    current_section = None
    for entry in entries:
        if entry["section"] != current_section:
            current_section = entry["section"]
            print(f"\n{'─' * 80}")
            print(f"  {current_section}")
            print(f"{'─' * 80}")

        print(f"\n  SANGRIA:      {entry['sangria']}")
        print(f"  Translation:  {entry['translation']}")
        print(f"  Reliability:  {entry['reliability']}")
        print(f"  Source:       {entry['source']}")
        print(f"  {'·' * 60}")


def search_entries(entries, query, field=None):
    """
    Search entries by a query string.
    
    Args:
        entries: List of entry dicts
        query: Search string (case-insensitive)
        field: Optional field to restrict search to.
               One of: "sangria", "translation", "source", or None for all fields.
    
    Returns:
        List of matching entry dicts
    """
    query = query.lower()
    results = []

    for entry in entries:
        if field:
            # Search only in the specified field
            if query in entry[field].lower():
                results.append(entry)
        else:
            # Search across all fields
            if (query in entry["sangria"].lower() or
                query in entry["translation"].lower() or
                query in entry["source"].lower()):
                results.append(entry)

    return results


def print_help():
    """Print usage instructions."""
    print("=" * 80)
    print("SANGRIA Translations - Ryōshū (Limbus Company)")
    print("=" * 80)
    print()
    print("Usage:")
    print("  python scrape_sangria.py                    Show all entries (uses cache)")
    print("  python scrape_sangria.py <query>            Search all fields (uses cache)")
    print("  python scrape_sangria.py -s <query>         Search SANGRIA field")
    print("  python scrape_sangria.py -t <query>         Search Translation field")
    print("  python scrape_sangria.py -src <query>       Search Source field")
    print("  python scrape_sangria.py --refresh          Force re-fetch from website")
    print("  python scrape_sangria.py --cache-age        Show cache age info")
    print("  python scrape_sangria.py -h                 Show this help")
    print()
    print("Cache:")
    print(f"  Cache file: {CACHE_FILE}")
    print(f"  Cache duration: {CACHE_DURATION}")
    print("  Data is cached locally to reduce website requests.")
    print("  Use --refresh to force an update.")
    print()
    print("Examples:")
    print('  python scrape_sangria.py "confirmed"        Find all confirmed entries')
    print('  python scrape_sangria.py -s "LD"            Find entry with SANGRIA "LD"')
    print('  python scrape_sangria.py -t "snap"          Search translations containing "snap"')
    print('  python scrape_sangria.py -src "identity"    Search sources containing "identity"')
    print('  python scrape_sangria.py --refresh          Update cached data from website')
    print()


def main():
    # Handle special flags that don't need data
    if len(sys.argv) == 2 and sys.argv[1] == "--cache-age":
        print("=" * 80)
        print("Cache Information")
        print("=" * 80)
        print(f"  File:     {CACHE_FILE}")
        print(f"  Exists:   {'Yes' if os.path.exists(CACHE_FILE) else 'No'}")
        print(f"  Age:      {get_cache_age()}")
        print(f"  Max age:  {CACHE_DURATION}")
        print(f"  Fresh:    {'Yes' if is_cache_fresh() else 'No'}")
        print()
        return

    if len(sys.argv) == 2 and sys.argv[1] == "-h":
        print_help()
        return

    # Determine if we need to force refresh
    force_refresh = "--refresh" in sys.argv

    # Remove --refresh from args so it doesn't interfere with search
    args = [a for a in sys.argv[1:] if a != "--refresh"]

    # Load data (from cache or website)
    entries, source = load_or_fetch_data(force_refresh=force_refresh)

    if not args:
        # No search args: show all entries
        print("=" * 80)
        print("SANGRIA Translations - Ryōshū (Limbus Company)")
        print(f"Data source: {source}")
        print("=" * 80)
        display_entries(entries)
        print(f"\n{'=' * 80}")
        print(f"  Total entries: {len(entries)}")
        print(f"{'=' * 80}")

    elif args[0] in ("-s", "-t", "-src"):
        # Field-specific search
        field_map = {
            "-s": "sangria",
            "-t": "translation",
            "-src": "source",
        }
        field = field_map[args[0]]
        if len(args) < 2:
            print(f"Error: Missing search query for flag {args[0]}")
            print_help()
            return

        query = " ".join(args[1:])
        results = search_entries(entries, query, field=field)

        print("=" * 80)
        print(f"Search results for '{query}' in [{field}]")
        print(f"Data source: {source}")
        print("=" * 80)
        display_entries(results)
        print(f"\n{'=' * 80}")
        print(f"  Found: {len(results)} / {len(entries)} entries")
        print(f"{'=' * 80}")

    else:
        # General search across all fields
        query = " ".join(args)
        results = search_entries(entries, query)

        print("=" * 80)
        print(f"Search results for '{query}' (all fields)")
        print(f"Data source: {source}")
        print("=" * 80)
        display_entries(results)
        print(f"\n{'=' * 80}")
        print(f"  Found: {len(results)} / {len(entries)} entries")
        print(f"{'=' * 80}")


if __name__ == "__main__":
    main()