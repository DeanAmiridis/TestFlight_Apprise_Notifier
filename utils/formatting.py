from __future__ import annotations
import re
import requests

from datetime import datetime

def format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")
    
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

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

    # Match "Join the (AppName) beta - TestFlight - Apple"
    m = re.search(r"Join the (.+) beta - TestFlight - Apple", raw_title)
    if m:
        return m.group(1).strip()

    # Fallback: strip " on TestFlight"
    name = re.sub(r"\s+on\s+TestFlight\s*$", "", raw_title, flags=re.IGNORECASE).strip()
    return name or "UnknownApp"

def get_app_name(base_url: str, tf_id: str) -> str:
    url = _safe_join(base_url, tf_id)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
    except Exception:
        return "UnknownApp"
    raw_title = _extract_title_html(resp.text)
    return _normalize_app_name(raw_title)

def format_link(base_url: str, tf_id: str) -> str:
    return f"{base_url.rstrip('/')}/{tf_id.lstrip('/')}"

def format_notification_link(base_url: str, tf_id: str) -> str:
    app_name = get_app_name(base_url, tf_id)
    return f"{app_name}-{format_link(base_url, tf_id)}"