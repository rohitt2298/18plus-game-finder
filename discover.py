
import re
import requests
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse, quote_plus

ITCH_FEEDS = [
    "https://itch.io/feed/new.xml",
    "https://itch.io/games/newest.xml",
    "https://itch.io/games/tag-visual-novel.xml",
    "https://itch.io/games/tag-dating-sim.xml",
    "https://itch.io/games/tag-simulation.xml",
    "https://itch.io/games/tag-nsfw.xml",
]

STEAM_SEARCHES = [
    "adult visual novel",
    "mature visual novel",
    "dating simulator",
    "romance visual novel",
    "NSFW game",
    "adult simulation",
    "eroge",
]

HEADERS = {
    "User-Agent": "AFTERDARK-GameDiscovery/1.0"
}


def clean_text(value):
    value = unescape(value or "")
    value = re.sub(r"<[^>]*>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def discover_itch_games(session):
    games = []
    errors = []

    for feed in ITCH_FEEDS:
        try:
            response = session.get(feed, timeout=20)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            for item in root.findall(".//item"):
                title = clean_text(
                    item.findtext("plainTitle")
                    or item.findtext("title")
                )

                link = (
                    item.findtext("link")
                    or item.findtext("guid")
                    or ""
                ).strip()

                host = urlparse(link).hostname or ""

                if not title:
                    continue

                if not (
                    host == "itch.io"
                    or host.endswith(".itch.io")
                ):
                    continue

                description = clean_text(
                    item.findtext("description")
                )

                image = (
                    item.findtext("imageurl") or ""
                ).strip()

                price = (
                    item.findtext("price") or ""
                ).strip()

                platform_node = item.find("platforms")
                platforms = []

                if platform_node is not None:
                    for platform in platform_node:
                        if (platform.text or "").strip().lower() == "yes":
                            name = platform.tag.lower()

                            if name == "html":
                                platforms.append("Browser")
                            elif name == "android":
                                platforms.append("Android")
                            elif name in ("windows", "linux", "osx"):
                                platforms.append("PC")

                games.append({
                    "game_id": link,
                    "title": title,
                    "platform": " / ".join(sorted(set(platforms))) or "Unknown",
                    "source": "itch.io",
                    "genre": "Unknown",
                    "art_style": "Unknown",
                    "price_type": (
                        "Free" if price in ("$0.00", "0.00")
                        else "Paid / Other" if price
                        else "Unknown"
                    ),
                    "rating": None,
                    "rating_count": None,
                    "views": None,
                    "downloads": None,
                    "trend_score": None,
                    "stats_source": "Not publicly available",
                    "last_verified": "",
                    "description": description[:500],
                    "official_url": link,
                    "cover_url": image,
                    "adult_verified": False,
                    "listing_status": "pending_review",
                    "f95_search_url": (
                        "https://f95zone.to/search/?q="
                        + quote_plus(title)
                    )
                })

        except Exception as error:
            errors.append(f"itch.io: {error}")

    return games, errors


def discover_steam_games(session):
    games = []
    errors = []
    seen = set()

    for term in STEAM_SEARCHES:
        try:
            response = session.get(
                "https://store.steampowered.com/api/storesearch/",
                params={
                    "term": term,
                    "l": "english",
                    "cc": "us"
                },
                timeout=20
            )

            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                title = clean_text(item.get("name", ""))
                app_id = item.get("id")

                if not title or not app_id or app_id in seen:
                    continue

                seen.add(app_id)

                image = item.get("tiny_image", "")

                games.append({
                    "game_id": f"steam-{app_id}",
                    "title": title,
                    "platform": "PC",
                    "source": "Steam",
                    "genre": "Unknown",
                    "art_style": "Unknown",
                    "price_type": "Unknown",
                    "rating": None,
                    "rating_count": None,
                    "views": None,
                    "downloads": None,
                    "trend_score": None,
                    "stats_source": "Not publicly available",
                    "last_verified": "",
                    "description": "Pending manual review",
                    "official_url": (
                        f"https://store.steampowered.com/app/{app_id}/"
                    ),
                    "cover_url": image,
                    "adult_verified": False,
                    "listing_status": "pending_review",
                    "f95_search_url": (
                        "https://f95zone.to/search/?q="
                        + quote_plus(title)
                    )
                })

        except Exception as error:
            errors.append(f"Steam ({term}): {error}")

    return games, errors


# IMPORTANT: Keep this function at the LEFT EDGE.
# Do not put spaces before def.

def discover_games():
    session = requests.Session()
    session.headers.update(HEADERS)

    itch_games, itch_errors = discover_itch_games(session)
    steam_games, steam_errors = discover_steam_games(session)

    combined = itch_games + steam_games

    unique = []
    seen = set()

    for game in combined:
        key = game.get("game_id") or game.get("official_url")

        if key and key not in seen:
            seen.add(key)
            unique.append(game)

    errors = itch_errors + steam_errors

    if not unique and errors:
        raise RuntimeError(
            "Discovery sources failed: " + " | ".join(errors[:5])
        )

    return unique
