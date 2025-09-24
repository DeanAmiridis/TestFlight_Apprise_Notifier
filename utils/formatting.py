from __future__ import annotations
import re
import aiohttp

from datetime import datetime

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

# Cache for app names and icons
app_name_cache = {}
app_icon_cache = {}

DEFAULT_TIMEOUT = 10
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _safe_join(base_url: str, tf_id: str) -> str:
    return f"{base_url.rstrip('/')}/{tf_id.lstrip('/')}"


def _extract_title_html(html: str) -> str | None:
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return None
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return None


def _normalize_app_name(raw_title: str | None) -> str:
    if not raw_title:
        return "UnknownApp"

    # Remove "Step X" patterns
    raw_title = re.sub(r"Step \d+", "", raw_title, flags=re.IGNORECASE).strip()

    # Match "Join the (AppName) beta - TestFlight - Apple"
    m = re.search(r"Join the (.+) beta - TestFlight - Apple", raw_title)
    if m:
        return m.group(1).strip()

    # Fallback: strip " on TestFlight"
    name = re.sub(r"\s+on\s+TestFlight\s*$", "", raw_title, flags=re.IGNORECASE).strip()
    return name or "UnknownApp"


async def get_app_name(base_url: str, tf_id: str) -> str:
    cache_key = f"{base_url}:{tf_id}"
    if cache_key in app_name_cache:
        return app_name_cache[cache_key]

    url = _safe_join(base_url, tf_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=HEADERS,
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
            ) as resp:
                resp.raise_for_status()
                html = await resp.text()
                if BeautifulSoup is not None:
                    soup = BeautifulSoup(html, "html.parser")
                    # Use the specific selector for app name
                    app_element = soup.select_one(
                        "#steps > div > div > div.gradient-column.app-gradient > div.app-steps > div.step1"
                    )
                    if app_element:
                        raw_name = app_element.text.strip()
                        app_name = _normalize_app_name(raw_name)
                        app_name_cache[cache_key] = app_name
                        return app_name
                # Fallback to title
                raw_title = _extract_title_html(html)
                app_name = _normalize_app_name(raw_title)
                app_name_cache[cache_key] = app_name
                return app_name
    except Exception:
        app_name = "UnknownApp"
        app_name_cache[cache_key] = app_name
        return app_name


async def get_app_icon(base_url: str, tf_id: str) -> str:
    cache_key = f"{base_url}:{tf_id}"
    if cache_key in app_icon_cache:
        return app_icon_cache[cache_key]

    url = _safe_join(base_url, tf_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=HEADERS,
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
            ) as resp:
                resp.raise_for_status()
                html = await resp.text()
                if BeautifulSoup is not None:
                    soup = BeautifulSoup(html, "html.parser")
                    # Assume the app icon is the first img tag or with class 'app-icon'
                    img = soup.find("img", class_="app-icon") or soup.find("img")
                    if img and img.get("src"):
                        icon_url = img["src"]
                        # Make absolute if relative
                        if icon_url.startswith("/"):
                            icon_url = f"https://testflight.apple.com{icon_url}"
                        app_icon_cache[cache_key] = icon_url
                        return icon_url
    except Exception:
        pass
    # Default icon or empty
    icon_url = ""
    app_icon_cache[cache_key] = icon_url
    return icon_url


def format_link(base_url: str, tf_id: str) -> str:
    return f"{base_url.rstrip('/')}/{tf_id.lstrip('/')}"


async def format_notification_link(base_url: str, tf_id: str) -> str:
    app_name = await get_app_name(base_url, tf_id)
    return f"Slots available for {app_name}: {format_link(base_url, tf_id)}"


def format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")
