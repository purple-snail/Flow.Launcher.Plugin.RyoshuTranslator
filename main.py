import json
import sys
import os
import gzip
import urllib.request
import urllib.error
from html.parser import HTMLParser
from datetime import datetime, timedelta

URL = "https://limbuscompany.wiki.gg/wiki/Ry%C5%8Dsh%C5%AB"
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sangria_cache.json")
CACHE_DURATION = timedelta(hours=1)
PLUGIN_ICON = "icon.webp"


class TableParser(HTMLParser):
    """Parse the SANGRIA table from the wiki HTML."""

    def __init__(self):
        super().__init__()
        self.entries = []
        self.current_section = "General"
        self.in_table = False
        self.in_tr = False
        self.in_td = False
        self.in_th = False
        self.cell_count = 0
        self.current_cells = []
        self.current_cell_text = ""
        self.is_colspan = False
        self.colspan_value = 1

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "table" and "wikitable" in attrs_dict.get("class", ""):
            self.in_table = True
            return
        if not self.in_table:
            return
        if tag == "tr":
            self.in_tr = True
            self.current_cells = []
            self.cell_count = 0
            return
        if tag in ("td", "th") and self.in_tr:
            if tag == "td":
                self.in_td = True
            else:
                self.in_th = True
            self.current_cell_text = ""
            self.colspan_value = int(attrs_dict.get("colspan", "1"))
            self.is_colspan = self.colspan_value > 1
            return

    def handle_endtag(self, tag):
        if tag == "table" and self.in_table:
            self.in_table = False
            return
        if not self.in_table:
            return
        if tag == "tr":
            self.in_tr = False
            self._process_row()
            return
        if (tag == "td" and self.in_td) or (tag == "th" and self.in_th):
            text = self.current_cell_text.strip()
            self.current_cells.append(text)
            self.cell_count += 1
            self.in_td = False
            self.in_th = False
            return

    def handle_data(self, data):
        if self.in_td or self.in_th:
            self.current_cell_text += data

    def handle_entityref(self, name):
        if self.in_td or self.in_th:
            char = {
                "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'",
                "ndash": "\u2013", "mdash": "\u2014", "nbsp": " ",
                "ouml": "\u00f6", "auml": "\u00e4", "uuml": "\u00fc",
                "Ouml": "\u00d6", "Auml": "\u00c4", "Uuml": "\u00dc", "szlig": "\u00df",
            }.get(name, f"&{name};")
            self.current_cell_text += char

    def _process_row(self):
        if self.cell_count == 0:
            return
        if self.is_colspan and self.colspan_value >= 3:
            if self.current_cells:
                self.current_section = self.current_cells[0]
            return
        if len(self.current_cells) >= 2:
            if self.current_cells[0] == "SANGRIA" and self.current_cells[1] == "Translation":
                return
        if len(self.current_cells) >= 4:
            self.entries.append({
                "section": self.current_section,
                "sangria": self.current_cells[0],
                "translation": self.current_cells[1],
                "reliability": self.current_cells[2],
                "source": self.current_cells[3],
            })


def fetch_sangria_data():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Cache-Control": "max-age=0",
            "DNT": "1",
        }
        req = urllib.request.Request(URL, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read()
            info = response.info()
            content_encoding = info.get("Content-Encoding", "")
            if content_encoding == "gzip":
                raw = gzip.decompress(raw)
            elif content_encoding == "deflate":
                raw = gzip.decompress(raw)
            html = raw.decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        return [], f"Failed to fetch: {e}"
    parser = TableParser()
    try:
        parser.feed(html)
    except Exception as e:
        return [], f"Failed to parse HTML: {e}"
    return parser.entries, None


def save_cache(entries):
    cache_data = {"timestamp": datetime.now().isoformat(), "entries": entries}
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        return True
    except (OSError, IOError):
        return False


def load_cache():
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache_data = json.load(f)
    return cache_data["entries"], cache_data["timestamp"]


def is_cache_fresh():
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        _, timestamp_str = load_cache()
        cache_time = datetime.fromisoformat(timestamp_str)
        return datetime.now() - cache_time < CACHE_DURATION
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return False


def get_cache_info():
    if not os.path.exists(CACHE_FILE):
        return "No cache exists."
    try:
        entries, timestamp_str = load_cache()
        cache_time = datetime.fromisoformat(timestamp_str)
        age = datetime.now() - cache_time
        if age < timedelta(minutes=1):
            age_str = "Less than a minute old"
        elif age < timedelta(hours=1):
            age_str = f"{int(age.total_seconds() // 60)} minute(s) old"
        elif age < timedelta(days=1):
            hours = int(age.total_seconds() // 3600)
            minutes = int((age.total_seconds() % 3600) // 60)
            age_str = f"{hours} hour(s), {minutes} minute(s) old"
        else:
            age_str = f"{age.days} day(s) old"
        status = "Fresh" if is_cache_fresh() else "Stale"
        return f"{len(entries)} entries | {age_str} | {status}"
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return "Cache is corrupted."


def load_or_fetch_data(force_refresh=False):
    if force_refresh:
        entries, error = fetch_sangria_data()
        if error:
            return entries, error
        save_cache(entries)
        return entries, None
    if is_cache_fresh():
        try:
            entries, _ = load_cache()
            return entries, None
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            pass
    entries, error = fetch_sangria_data()
    if error:
        return entries, error
    save_cache(entries)
    return entries, None


def search_entries(entries, query):
    """Search entries by SANGRIA abbreviation (case-insensitive)."""
    query = query.lower()
    results = []
    for entry in entries:
        if query in entry["sangria"].lower():
            results.append(entry)
    return results


def make_result(title, subtitle, action=None):
    result = {"Title": title, "SubTitle": subtitle, "IcoPath": PLUGIN_ICON}
    if action:
        result["JsonRPCAction"] = {
            "method": action["method"],
            "parameters": action.get("parameters", []),
            "dontHideAfterAction": action.get("dont_hide", False),
        }
    return result


def build_menu_results():
    return [
        make_result(
            "🔄 Refresh Cache",
            "Force re-fetch data from the wiki",
            {"method": "query", "parameters": ["!refresh"]},
        ),
        make_result(
            "ℹ️ Cache Info",
            f"Status: {get_cache_info()}",
            {"method": "query", "parameters": ["!cache"], "dont_hide": True},
        ),
    ]


def build_entry_results(entries):
    results = []
    for entry in entries[:50]:
        title = f"{entry['sangria']}  ->  {entry['translation']}"
        subtitle = f"[{entry['section']}] {entry['reliability']} | {entry['source']}"
        copy_text = f"{entry['sangria']}: {entry['translation']} ({entry['reliability']}) - {entry['source']}"
        results.append(make_result(
            title, subtitle, {"method": "copy", "parameters": [copy_text]},
        ))
    if len(entries) > 50:
        results.append(make_result(
            f"... and {len(entries) - 50} more entries",
            "Refine your search to see more specific results",
        ))
    return results


def handle_query(search_params):
    if not search_params or (len(search_params) == 1 and search_params[0].strip() == ""):
        return build_menu_results()

    query = " ".join(search_params).strip()
    query_lower = query.lower()

    if query_lower == "!refresh":
        entries, error = load_or_fetch_data(force_refresh=True)
        if error:
            return [make_result("Error", error)]
        return [make_result("Cache Refreshed", f"Loaded {len(entries)} entries from the wiki")]

    if query_lower == "!cache":
        return [make_result("Cache Information", get_cache_info())]

    entries, error = load_or_fetch_data()
    if error:
        return [make_result("Error", error)]

    results = search_entries(entries, query)

    if not results:
        return [make_result("No Results", f"No SANGRIA entries found matching '{query}'")]

    return build_entry_results(results)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"result": [make_result("Error", "No input provided")]}))
        return
    try:
        request = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print(json.dumps({"result": [make_result("Error", "Invalid JSON input")]}))
        return
    method = request.get("method", "")
    if method == "query":
        search_params = request.get("parameters", [])
        results = handle_query(search_params)
        print(json.dumps({"result": results}))
    else:
        print(json.dumps({"result": []}))


if __name__ == "__main__":
    main()