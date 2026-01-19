"""
Fetch québécismes from multiple sources.

Sources:
1. Données Québec (OQLF) - Official terminology CSV
2. Le Caméléon - ~650 québécismes with definitions
3. Wiktionary API - Category "français du Québec"
4. Exionnaire - 456 words list

Output: data/quebecismes/<source>.csv
"""

import csv
import json
import re
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from html.parser import HTMLParser

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
QUEBECISMES_DIR = PROJECT_ROOT / "data" / "quebecismes"

# Ensure output directory exists
QUEBECISMES_DIR.mkdir(parents=True, exist_ok=True)

# User agent for requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fetch_url(url: str, retries: int = 3, delay: float = 1.0) -> str:
    """Fetch URL content with retries."""
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(retries):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8")
        except (HTTPError, URLError) as e:
            print(f"  Attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)

    raise Exception(f"Failed to fetch {url} after {retries} attempts")


# =============================================================================
# 1. Données Québec (OQLF)
# =============================================================================

def fetch_donnees_quebec():
    """Download OQLF terminological data from Données Québec."""
    print("\n" + "=" * 60)
    print("1. Données Québec (OQLF)")
    print("=" * 60)

    # Official terms CSV (smaller, more relevant)
    url = "https://www.donneesquebec.ca/recherche/dataset/59f49727-1a5a-4f32-a774-4c06c0553d69/resource/882453c2-93c3-4204-b5ff-6d6297082ad9/download/termes_officialises_2026-01-14.csv"
    output_path = QUEBECISMES_DIR / "oqlf_termes_officialises.csv"

    print(f"  URL: {url}")
    print(f"  Downloading...")

    try:
        content = fetch_url(url)

        # Save raw file
        output_path.write_text(content, encoding="utf-8")

        # Count entries
        lines = content.strip().split("\n")
        print(f"  Saved: {output_path}")
        print(f"  Entries: {len(lines) - 1} (excluding header)")

        return True
    except Exception as e:
        print(f"  Error: {e}")
        print("  Trying alternative URL...")

        # Try fetching the resource list page to find current URL
        try:
            alt_url = "https://www.donneesquebec.ca/recherche/api/3/action/package_show?id=donnees-linguistiques"
            data = json.loads(fetch_url(alt_url))

            for resource in data.get("result", {}).get("resources", []):
                if "termes_officialis" in resource.get("url", "").lower():
                    print(f"  Found: {resource['url']}")
                    content = fetch_url(resource["url"])
                    output_path.write_text(content, encoding="utf-8")
                    lines = content.strip().split("\n")
                    print(f"  Saved: {output_path}")
                    print(f"  Entries: {len(lines) - 1}")
                    return True
        except Exception as e2:
            print(f"  Alternative also failed: {e2}")

        return False


# =============================================================================
# 2. Le Caméléon
# =============================================================================

class CameleonParser(HTMLParser):
    """Parse québécismes from lecameleon.eu."""

    def __init__(self):
        super().__init__()
        self.entries = []
        self.current_text = []
        self.in_content = False
        self.capture = False

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "li"):
            self.capture = True
            self.current_text = []

    def handle_endtag(self, tag):
        if tag in ("p", "li") and self.capture:
            text = "".join(self.current_text).strip()
            if text:
                self.entries.append(text)
            self.capture = False

    def handle_data(self, data):
        if self.capture:
            self.current_text.append(data)


def parse_cameleon_entry(text: str) -> dict | None:
    """Parse a single entry like 'ACHIGAN n.m. Black-bass (poisson).'"""
    # Pattern: WORD pos. definition
    # pos can be: n.m., n.f., vt., vi., v., adj., adv., loc., etc.
    pattern = r"^([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ][A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ\s\-\']+)\s+(n\.m\.|n\.f\.|n\.|v\.t\.|v\.i\.|v\.|adj\.|adv\.|loc\.|prép\.|conj\.|interj\.|pron\.)\s*(.*)$"

    match = re.match(pattern, text.strip(), re.IGNORECASE)
    if match:
        word = match.group(1).strip()
        pos = match.group(2).strip()
        definition = match.group(3).strip()

        # Normalize POS
        pos_map = {
            "n.m.": "n.m.",
            "n.f.": "n.f.",
            "n.": "n.",
            "v.t.": "v.t.",
            "v.i.": "v.i.",
            "v.": "v.",
            "adj.": "adj.",
            "adv.": "adv.",
            "loc.": "loc.",
            "prép.": "prép.",
            "conj.": "conj.",
            "interj.": "interj.",
            "pron.": "pron.",
        }
        pos = pos_map.get(pos.lower(), pos)

        return {
            "word": word.title() if word.isupper() else word,
            "pos": pos,
            "definition": definition
        }

    return None


def fetch_cameleon():
    """Fetch québécismes from lecameleon.eu."""
    print("\n" + "=" * 60)
    print("2. Le Caméléon")
    print("=" * 60)

    url = "https://www.lecameleon.eu/quebecismes.php"
    output_path = QUEBECISMES_DIR / "cameleon_quebecismes.csv"

    print(f"  URL: {url}")
    print(f"  Fetching...")

    try:
        html = fetch_url(url)

        entries = []

        # Site structure:
        # <span class="ecriture2">WORD </span>
        # <span class="ecriture4"> pos. </span>
        # <span class="ecriture3"> definition</span>

        # Pattern for the specific site structure
        pattern = r'<span class="ecriture2">([^<]+)</span>\s*<span class="ecriture4">([^<]+)</span>\s*<span class="ecriture3">([^<]*)</span>'

        for match in re.finditer(pattern, html, re.IGNORECASE | re.DOTALL):
            word = match.group(1).strip()
            pos = match.group(2).strip()
            definition = match.group(3).strip()

            # Decode HTML entities
            import html as html_module
            word = html_module.unescape(word)
            pos = html_module.unescape(pos)
            definition = html_module.unescape(definition)

            # Skip very short
            if len(word) < 2:
                continue

            # Skip if looks like navigation
            if word.lower() in ("accueil", "contact", "menu", "page", "a", "b", "c"):
                continue

            # Normalize word (title case)
            word_normalized = word.strip()
            if word_normalized.isupper():
                word_normalized = word_normalized.title()

            # Skip duplicates
            if any(e["word"].upper() == word_normalized.upper() for e in entries):
                continue

            entries.append({
                "word": word_normalized,
                "pos": pos.lower().strip(),
                "definition": definition
            })

        # Also try alternative pattern (some entries might be formatted differently)
        alt_pattern = r'class="ecriture2">([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇŒ][A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇŒ\s\-\']*?)\s*</span>'

        for match in re.finditer(alt_pattern, html):
            word = match.group(1).strip()

            if len(word) < 2:
                continue

            word_normalized = word.title() if word.isupper() else word

            # Skip if already found
            if any(e["word"].upper() == word_normalized.upper() for e in entries):
                continue

            entries.append({
                "word": word_normalized,
                "pos": "",
                "definition": ""
            })

        # Save to CSV
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["word", "pos", "definition"])
            writer.writeheader()
            writer.writerows(entries)

        print(f"  Saved: {output_path}")
        print(f"  Entries: {len(entries)}")

        # Save raw HTML for debugging if few entries found
        if len(entries) < 50:
            debug_path = QUEBECISMES_DIR / "cameleon_debug.html"
            debug_path.write_text(html, encoding="utf-8")
            print(f"  Debug HTML saved: {debug_path}")

        return True
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# 3. Wiktionary API
# =============================================================================

def fetch_wiktionary():
    """Fetch words from Wiktionary category 'français du Québec'."""
    print("\n" + "=" * 60)
    print("3. Wiktionary (français du Québec)")
    print("=" * 60)

    base_url = "https://fr.wiktionary.org/w/api.php"
    output_path = QUEBECISMES_DIR / "wiktionary_quebecismes.csv"

    # Categories to fetch (will be URL-encoded)
    categories = [
        "Catégorie:français du Québec",
        "Catégorie:Québécismes",
    ]

    all_words = set()

    for category in categories:
        print(f"  Category: {category}")

        continue_token = None
        page_count = 0

        while True:
            # Build URL with proper encoding
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category,
                "cmlimit": "500",
                "cmtype": "page",
                "format": "json"
            }
            if continue_token:
                params["cmcontinue"] = continue_token

            url = base_url + "?" + urlencode(params)

            try:
                data = json.loads(fetch_url(url))

                members = data.get("query", {}).get("categorymembers", [])
                for member in members:
                    title = member.get("title", "")
                    # Skip category pages and templates
                    if not title.startswith(("Catégorie:", "Modèle:", "Annexe:")):
                        all_words.add(title)

                page_count += 1
                print(f"    Page {page_count}: +{len(members)} entries")

                # Check for continuation
                if "continue" in data:
                    continue_token = data["continue"].get("cmcontinue")
                else:
                    break

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"    Error: {e}")
                break

    # Save to CSV
    words_list = sorted(all_words)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word"])
        for word in words_list:
            writer.writerow([word])

    print(f"  Saved: {output_path}")
    print(f"  Total unique entries: {len(words_list)}")

    return True


# =============================================================================
# 4. Exionnaire
# =============================================================================

class ExionnaireParser(HTMLParser):
    """Parse québécismes list from exionnaire.com."""

    def __init__(self):
        super().__init__()
        self.words = []
        self.in_link = False
        self.current_word = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            # Links to word definitions
            if "/definir/" in href or "titre=" in href:
                self.in_link = True
                self.current_word = ""

    def handle_endtag(self, tag):
        if tag == "a" and self.in_link:
            if self.current_word.strip():
                self.words.append(self.current_word.strip())
            self.in_link = False

    def handle_data(self, data):
        if self.in_link:
            self.current_word += data


def fetch_exionnaire():
    """Fetch québécismes from exionnaire.com."""
    print("\n" + "=" * 60)
    print("4. Exionnaire")
    print("=" * 60)

    # Correct URL format
    base_url = "https://www.dictionnaire.exionnaire.com/mot-diese/parler_quebec"
    alt_url = "https://www.listes.exionnaire.com/parler-quebec"
    output_path = QUEBECISMES_DIR / "exionnaire_quebecismes.csv"

    all_words = set()

    # Try multiple URL formats
    urls_to_try = [
        f"{alt_url}.html",
        f"{base_url}.html",
        "https://www.exionnaire.com/listes/parler-quebec.html",
    ]

    html = None
    for url in urls_to_try:
        print(f"  Trying: {url}")
        try:
            html = fetch_url(url)
            print(f"  Success!")
            break
        except Exception as e:
            print(f"    Failed: {e}")

    if not html:
        print("  All URLs failed, skipping...")
        # Save empty file
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["word"])
        return False

    # Extract words from HTML
    # Look for words in links to definitions
    patterns = [
        r'href="[^"]*definir/([^"]+)"',  # Links to definitions
        r'href="[^"]*titre=([^"&]+)"',   # Title parameter
        r'>([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇŒ]{2,})</a>',  # Uppercase words in links
        r'<li[^>]*>([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇŒ][A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇŒa-zàâäéèêëïîôùûüçœ\-\' ]+)',  # Words in list items
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, html):
            word = match.group(1).strip()
            # Decode URL encoding if needed
            word = word.replace("%20", " ").replace("_", " ")
            # Filter valid words
            if len(word) >= 2 and len(word) <= 40:
                if re.match(r"^[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇŒa-zàâäéèêëïîôùûüçœ\-\' ]+$", word):
                    all_words.add(word.upper())

    # Save to CSV
    words_list = sorted(all_words)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word"])
        for word in words_list:
            writer.writerow([word])

    print(f"  Saved: {output_path}")
    print(f"  Total entries: {len(words_list)}")

    # Save debug HTML if few results
    if len(words_list) < 10:
        debug_path = QUEBECISMES_DIR / "exionnaire_debug.html"
        debug_path.write_text(html[:50000], encoding="utf-8")
        print(f"  Debug HTML saved: {debug_path}")

    return len(words_list) > 0


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("QUÉBÉCISMES FETCHER")
    print("=" * 60)
    print(f"Output directory: {QUEBECISMES_DIR}")

    results = {}

    # 1. Données Québec
    results["donnees_quebec"] = fetch_donnees_quebec()

    # 2. Le Caméléon
    results["cameleon"] = fetch_cameleon()

    # 3. Wiktionary
    results["wiktionary"] = fetch_wiktionary()

    # 4. Exionnaire
    results["exionnaire"] = fetch_exionnaire()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for source, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {source}")

    print(f"\nOutput files in: {QUEBECISMES_DIR}")

    # List output files
    for f in sorted(QUEBECISMES_DIR.glob("*.csv")):
        size = f.stat().st_size
        print(f"  - {f.name} ({size:,} bytes)")


if __name__ == "__main__":
    main()
