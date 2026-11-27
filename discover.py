import re
import time
import requests
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse, quote_plus

# Restrict automated discovery to feeds explicitly tagged NSFW/adult.
ITCH_FEEDS = [
    ("NSFW", "https://itch.io/games/tag-nsfw.xml"),
    ("Adult", "https://itch.io/games/tag-adult.xml"),
]
F95_FEED = "https://f95zone.to/sam/latest_alpha/latest_data.php?cmd=rss&cat=games"
MAX_PAGES_PER_FEED = 4
REQUEST_TIMEOUT = 18
USER_AGENT = "AFTERDARK-GameDiscovery/1.1"

# Conservative keyword screening. This is a basic safety filter, not moderation.
RISK_TERMS = re.compile(
    r"\b(loli|lolita|shota|underage|under.?age|school.?girl|school.?boy|"
    r"child|children|kid|minor|teen(?:age)?|young girl|young boy)\b",
    re.I,
)

def clean(value):
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def art_style_from_text(*values):
    text = " ".join(clean(v) for v in values).lower()
    if re.search(r"\b(2d|anime|manga|sprite|pixel art|hand.?drawn)\b", text):
        return "2D"
    if re.search(r"\b(3d|three.?dimensional|rendered|unity|unreal)\b", text):
        return "3D"
    return "Unknown"

def _platforms(item):
    found = []
    node = item.find("platforms")
    if node is not None:
        for child in list(node):
            if (child.text or "").strip().lower() == "yes":
                tag = child.tag.lower()
                if tag == "html":
                    found.append("Browser")
                elif tag == "android":
                    found.append("Android")
                elif tag in ("windows", "linux", "osx"):
                    found.append("PC")
    return " / ".join(sorted(set(found))) if found else "Unknown"

def _image(item):
    cover = (item.findtext("imageurl") or "").strip()
    if cover:
        return cover
    description = item.findtext("description") or ""
    match = re.search(r'<img[^>]+src=["\']([^"\']+)', description, re.I)
    return match.group(1) if match else ""

def _parse_feed(feed_url, source, label, pages=1):
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    games, errors = [], []
    seen = set()
    for page in range(1, pages + 1):
        try:
            response = session.get(feed_url, params={"page": page}, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            if not items:
                break
            for item in items:
                title = clean(item.findtext("plainTitle") or item.findtext("title"))
                link = (item.findtext("link") or item.findtext("guid") or "").strip()
                if not title or not link or link in seen:
                    continue
                host = (urlparse(link).hostname or "").lower()
                allowed = (host == "itch.io" or host.endswith(".itch.io")) if source == "itch.io" else host.endswith("f95zone.to")
                if not allowed:
                    continue
                description = clean(item.findtext("description"))
                categories = " ".join(clean(x.text) for x in item.findall("category"))
                if RISK_TERMS.search(" ".join((title, description, categories))):
                    continue
                seen.add(link)
                price = (item.findtext("price") or "").strip()
                price_type = "Free" if price in ("$0.00", "0.00") else ("Paid / other" if price else "Unknown")
                games.append({
                    "game_id": link,
                    "title": title,
                    "platform": _platforms(item) if source == "itch.io" else "Unknown",
                    "source": source,
                    "feed": label,
                    "genre": categories or "Unknown",
                    "art_style": art_style_from_text(title, description, categories),
                    "price_type": price_type,
                    "rating": None,
                    "rating_count": None,
                    "views": None,
                    "downloads": None,
                    "trend_score": None,
                    "stats_source": "Not supplied by source feed",
                    "last_verified": "",
                    "description": description[:450],
                    "official_url": link,
                    "cover_url": _image(item),
                    "adult_verified": False,
                    "listing_status": "unverified",
                })
            if len(items) < 30:
                break
            time.sleep(0.15)
        except Exception as exc:
            errors.append(f"{label} page {page}: {exc}")
    return games, errors

def discover_itch_games(max_pages=None):
    pages = max(1, min(int(max_pages or MAX_PAGES_PER_FEED), 10))
    games, errors = [], []
    for label, url in ITCH_FEEDS:
        found, issues = _parse_feed(url, "itch.io", label, pages)
        games.extend(found)
        errors.extend(issues)
    return games, errors

def discover_f95_games():
    return _parse_feed(F95_FEED, "F95Zone", "Latest F95Zone games", 1)

F95_SEARCH_TERMS = [
    "visual novel", "dating sim", "simulation", "RPG",
    "adventure", "Android", "Linux", "completed",
]

def discover_f95_links():
    links = []
    for term in F95_SEARCH_TERMS:
        links.append({
            "title": f"F95Zone: {term}",
            "source": "F95Zone",
            "description": "Open F95Zone search results. Listings remain hosted by F95Zone.",
            "official_url": "https://f95zone.to/search/?q=" + quote_plus(term),
            "cover_url": "",
            "platform": "F95Zone",
            "listing_status": "external link",
        })
    links.append({
        "title": "Browse F95Zone",
        "source": "F95Zone",
        "description": "Browse current game forums and threads on F95Zone.",
        "official_url": "https://f95zone.to/",
        "cover_url": "",
        "platform": "F95Zone",
        "listing_status": "external link",
    })
    return links

def discover_games(max_pages=None):
    itch_games, itch_errors = discover_itch_games(max_pages=max_pages)
    f95_games, f95_errors = discover_f95_games()
    return {
        "itch_games": itch_games,
        "f95_games": f95_games,
        "f95_links": discover_f95_links(),
        "errors": itch_errors + f95_errors,
    }
