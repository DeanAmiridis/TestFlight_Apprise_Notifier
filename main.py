import os
import re
import asyncio
import aiohttp
import uvicorn
import apprise
import threading
import logging
import signal
import random
import itertools
import time
from collections import deque
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime
from utils.notifications import send_notification, send_notification_async
from utils.formatting import (
    format_datetime,
    format_link,
    format_notification_link,
    get_app_icon,
    get_app_name,
    app_name_cache,
    app_icon_cache,
)
from utils.colors import print_green

# Circuit breaker for external requests
_request_failures = {}
_circuit_breaker_threshold = 5
_circuit_breaker_timeout = 300  # 5 minutes

# Global HTTP session and lock
_http_session = None
_session_lock = threading.Lock()


def is_circuit_breaker_open(url: str) -> bool:
    """Check if circuit breaker is open for a URL."""
    if url in _request_failures:
        failures, last_failure = _request_failures[url]
        if failures >= _circuit_breaker_threshold:
            if time.time() - last_failure < _circuit_breaker_timeout:
                return True
            else:
                # Reset circuit breaker after timeout
                del _request_failures[url]
    return False


def record_request_failure(url: str):
    """Record a request failure for circuit breaker."""
    if url not in _request_failures:
        _request_failures[url] = [0, 0]
    _request_failures[url][0] += 1
    _request_failures[url][1] = time.time()


def record_request_success(url: str):
    """Record a request success, resetting circuit breaker."""
    if url in _request_failures:
        del _request_failures[url]


async def get_http_session() -> aiohttp.ClientSession:
    """Get or create a shared HTTP session with connection pooling."""
    global _http_session
    if _http_session is None or _http_session.closed:
        with _session_lock:
            if _http_session is None or _http_session.closed:
                connector = aiohttp.TCPConnector(
                    limit=20,  # Connection pool size
                    limit_per_host=5,  # Connections per host
                    ttl_dns_cache=300,  # DNS cache TTL
                    use_dns_cache=True,
                    keepalive_timeout=60,
                    enable_cleanup_closed=True,
                )
                timeout = aiohttp.ClientTimeout(
                    total=30,  # Total timeout
                    connect=10,  # Connection timeout
                    sock_read=10,  # Socket read timeout
                )
                _http_session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        "User-Agent": "TestFlight-Notifier/1.0.5b",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                    },
                )
    return _http_session


# Version
__version__ = "1.0.5c"


def get_multiline_env_value(key: str) -> str:
    """Get environment value that may span multiple lines in .env file."""
    try:
        env_path = ".env"
        if not os.path.exists(env_path):
            return os.getenv(key, "")

        with open(env_path, "r") as f:
            lines = f.readlines()

        # Find the key and collect all continuation lines
        value_lines = []
        in_multiline = False

        for line in lines:
            line = line.strip()
            if line.startswith(f"{key}="):
                # Start of the key
                value_part = line[len(f"{key}=") :]
                if value_part.startswith('"') and value_part.endswith('"'):
                    # Quoted value - remove quotes and unescape
                    return value_part[1:-1].replace("\\n", "\n")
                else:
                    # Multi-line value starting
                    value_lines.append(value_part.rstrip(","))
                    in_multiline = True
            elif in_multiline and line and not line.startswith("#") and "=" not in line:
                # Continuation line
                value_lines.append(line.rstrip(","))
            elif in_multiline and (
                line.startswith(("APPRISE_URL=", "ID_LIST=", "INTERVAL_CHECK="))
                or not line
            ):
                # End of multi-line value (next key or empty line)
                break

        if value_lines:
            return "\n".join(value_lines)
        else:
            return os.getenv(key, "")
    except Exception:
        return os.getenv(key, "")


# Load environment variables
load_dotenv()

# Constants
TESTFLIGHT_URL = "https://testflight.apple.com/join/"
FULL_TEXT = "This beta is full."
NOT_OPEN_TEXT = "This beta isn't accepting any new testers right now."
id_list_raw = os.getenv("ID_LIST", "").split(",")
SLEEP_TIME = int(os.getenv("INTERVAL_CHECK", "10000"))  # in ms
TITLE_REGEX = re.compile(r"Join the (.+) beta - TestFlight - Apple")

# Parse Apprise URLs (supporting multi-line format)
apprise_url_raw = get_multiline_env_value("APPRISE_URL")
apprise_urls_raw = [
    url.strip().rstrip(",")
    for url in apprise_url_raw.replace("\n", ",").split(",")
    if url.strip()
]
HEARTBEAT_INTERVAL = 6 * 60 * 60  # 6 hours in seconds

# Configure logging
format_str = f"%(asctime)s - %(levelname)s - %(message)s [v{__version__}]"
logging.basicConfig(level=logging.INFO, format=format_str)

# Web logging handler to capture logs for web interface
log_entries: deque = deque(maxlen=100)  # Keep last 100 log entries
log_entries_lock = threading.Lock()  # Thread safety for log access
app_start_time = datetime.now()


class WebLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        with log_entries_lock:
            log_entries.append(log_entry)


def get_recent_logs(limit: int = 20) -> list:
    """Thread-safe function to get recent log entries."""
    with log_entries_lock:
        total_entries = len(log_entries)
        if total_entries == 0:
            return []

        # Use efficient slicing for better performance
        start_idx = max(0, total_entries - limit)
        return list(itertools.islice(log_entries, start_idx, total_entries))


# Add the web log handler to the root logger
web_handler = WebLogHandler()
logging.getLogger().addHandler(web_handler)

# Validate environment variables
ID_LIST = [tf_id.strip() for tf_id in id_list_raw if tf_id.strip()]
APPRISE_URLS = [url.strip() for url in apprise_urls_raw if url.strip()]

if not ID_LIST:
    logging.error(
        "Environment variable 'ID_LIST' is not set or contains only empty values."
    )
    raise ValueError("Environment variable 'ID_LIST' is required.")
if not APPRISE_URLS:
    logging.error(
        "Environment variable 'APPRISE_URL' is not set or contains only empty values."
    )
    raise ValueError("Environment variable 'APPRISE_URL' is required.")

# Initialize Apprise notifier
apobj = apprise.Apprise()
for url in APPRISE_URLS:
    if url:
        apobj.add(url)

# Global variables for dynamic ID management
id_list_lock = threading.Lock()
current_id_list = ID_LIST.copy()  # Thread-safe copy for monitoring

# Global variables for dynamic Apprise URL management
apprise_urls_lock = threading.Lock()
current_apprise_urls = APPRISE_URLS.copy()  # Thread-safe copy for monitoring


def get_current_id_list():
    """Thread-safe function to get current ID list."""
    with id_list_lock:
        return current_id_list.copy()


def get_current_apprise_urls():
    """Thread-safe function to get current Apprise URLs list."""
    with apprise_urls_lock:
        return current_apprise_urls.copy()


def update_env_file(key: str, new_values: list[str]):
    """Safely update the .env file with new values for a given key."""
    try:
        # Read current .env content
        env_path = ".env"
        if not os.path.exists(env_path):
            logging.error("Cannot update .env file: file does not exist")
            return False

        with open(env_path, "r") as f:
            lines = f.readlines()

        # Find and update the key line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                # Write each URL on its own line with a comma
                if new_values:
                    lines[i] = f"{key}={new_values[0]},\n"
                    # Insert additional lines after the first one
                    for j, url in enumerate(new_values[1:], 1):
                        lines.insert(i + j, f"{url},\n")
                else:
                    lines[i] = f"{key}=\n"
                updated = True
                break

        if not updated:
            # Add the key if it doesn't exist
            if new_values:
                lines.append(f"{key}={new_values[0]},\n")
                # Add additional lines
                for url in new_values[1:]:
                    lines.append(f"{url},\n")
            else:
                lines.append(f"{key}=\n")

        # Write back to file atomically
        with open(env_path, "w") as f:
            f.writelines(lines)

        logging.info(f"Updated .env file with {len(new_values)} {key} values")
        return True
    except Exception as e:
        logging.error(f"Failed to update .env file: {e}")
        return False


async def validate_testflight_id(tf_id):
    """Validate if a TestFlight ID exists and is accessible."""
    if not tf_id or not tf_id.strip():
        return False, "TestFlight ID cannot be empty"

    tf_id = tf_id.strip()
    testflight_url = format_link(TESTFLIGHT_URL, tf_id)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                testflight_url, headers={"Accept-Language": "en-us"}
            ) as response:
                if response.status == 404:
                    return False, "TestFlight ID not found (404)"
                elif response.status != 200:
                    return False, f"HTTP {response.status} error"

                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")

                # Check if it's a valid TestFlight page
                title = soup.find("title")
                if not title or "TestFlight" not in title.text:
                    return False, "Not a valid TestFlight page"

                return True, "Valid TestFlight ID"
    except Exception as e:
        return False, f"Error validating ID: {str(e)}"


def add_testflight_id(tf_id):
    """Add a TestFlight ID to the list and update .env file."""
    with id_list_lock:
        if tf_id in current_id_list:
            return False, "TestFlight ID already exists"

        new_list = current_id_list + [tf_id]
        if update_env_file("ID_LIST", new_list):
            current_id_list.append(tf_id)
            logging.info(f"Added TestFlight ID: {tf_id}")
            # Send notification about the addition
            total_ids = len(current_id_list)
            msg = f"TestFlight ID Added: {tf_id} (Total: {total_ids} IDs)"
            send_notification(msg, apobj)
            return True, "TestFlight ID added successfully"
        else:
            return False, "Failed to update .env file"


def remove_testflight_id(tf_id):
    """Remove a TestFlight ID from the list and update .env file."""
    with id_list_lock:
        if tf_id not in current_id_list:
            return False, "TestFlight ID not found"

        new_list = [id for id in current_id_list if id != tf_id]
        if update_env_file("ID_LIST", new_list):
            current_id_list.remove(tf_id)
            logging.info(f"Removed TestFlight ID: {tf_id}")
            # Send notification about the removal
            total_ids = len(current_id_list)
            msg = f"TestFlight ID Removed: {tf_id} (Total: {total_ids} IDs)"
            send_notification(msg, apobj)
            return True, "TestFlight ID removed successfully"
        else:
            return False, "Failed to update .env file"


def validate_apprise_url(url: str) -> tuple[bool, str]:
    """Validate if an Apprise URL is properly formatted and supported."""
    if not url or not url.strip():
        return False, "Apprise URL cannot be empty"

    url = url.strip()

    # Use Apprise library to validate the URL format
    try:
        # Create a temporary Apprise object to test URL validity
        test_apprise = apprise.Apprise()
        result = test_apprise.add(url)

        if result:
            # URL was successfully added, get service information
            urls = test_apprise.urls()
            if urls:
                service_info = urls[0]
                service_name = service_info.get("service_name", "Unknown Service")
                return True, f"Valid {service_name} URL"
            else:
                return True, "Valid Apprise URL"
        else:
            # Try to provide more specific error information
            msg = (
                "Invalid Apprise URL format. Please check "
                "the URL syntax and ensure the service is supported."
            )
            return False, msg

    except Exception as e:
        # Fallback to basic validation if Apprise validation fails
        logging.warning(f"Apprise validation error for URL {url}: {e}")

        # Basic URL validation - should start with a protocol
        supported_protocols = [
            # Productivity Based Notifications
            "apprise://",
            "apprises://",
            "ses://",
            "bark://",
            "barks://",
            "bluesky://",
            "chantify://",
            "discord://",
            "emby://",
            "embys://",
            "enigma2://",
            "enigma2s://",
            "fcm://",
            "feishu://",
            "flock://",
            "gchat://",
            "gotify://",
            "gotifys://",
            "growl://",
            "guilded://",
            "hassio://",
            "hassios://",
            "ifttt://",
            "join://",
            "kodi://",
            "kodis://",
            "kumulos://",
            "lametric://",
            "lark://",
            "line://",
            "mailgun://",
            "mastodon://",
            "mastodons://",
            "matrix://",
            "matrixs://",
            "mmost://",
            "mmosts://",
            "workflows://",
            "msteams://",
            "misskey://",
            "misskeys://",
            "mqtt://",
            "mqtts://",
            "ncloud://",
            "nclouds://",
            "nctalk://",
            "nctalks://",
            "notica://",
            "notifiarr://",
            "notifico://",
            "ntfy://",
            "o365://",
            "onesignal://",
            "opsgenie://",
            "pagerduty://",
            "pagertree://",
            "parsep://",
            "parseps://",
            "popcorn://",
            "prowl://",
            "pbul://",
            "pjet://",
            "pjets://",
            "push://",
            "pushed://",
            "pushme://",
            "pushover://",
            "pover://",
            "pushplus://",
            "psafer://",
            "psafers://",
            "pushy://",
            "pushdeer://",
            "pushdeers://",
            "qq://",
            "reddit://",
            "resend://",
            "revolt://",
            "rocket://",
            "rockets://",
            "rsyslog://",
            "ryver://",
            "sendgrid://",
            "sendpulse://",
            "schan://",
            "signal://",
            "signals://",
            "signl4://",
            "simplepush://",
            "slack://",
            "smtp2go://",
            "sparkpost://",
            "spike://",
            "splunk://",
            "victorops://",
            "spugpush://",
            "strmlabs://",
            "synology://",
            "synologys://",
            "syslog://",
            "tgram://",
            "twitter://",
            "twist://",
            "vapid://",
            "wxteams://",
            "wecombot://",
            "whatsapp://",
            "wxpusher://",
            "xbmc://",
            "xbmcs://",
            "zulip://",
            # SMS Notifications
            "atalk://",
            "aprs://",
            "sns://",
            "bulksms://",
            "bulkvs://",
            "burstsms://",
            "clickatell://",
            "clicksend://",
            "dapnet://",
            "d7sms://",
            "dingtalk://",
            "freemobile://",
            "httpsms://",
            "kavenegar://",
            "msgbird://",
            "msg91://",
            "plivo://",
            "seven://",
            "sfr://",
            "smpp://",
            "smpps://",
            "smseagle://",
            "smseagles://",
            "smsmgr://",
            "threema://",
            "twilio://",
            "voipms://",
            "nexmo://",
            # Desktop Notifications
            "dbus://",
            "qt://",
            "glib://",
            "kde://",
            "gnome://",
            "macosx://",
            "windows://",
            # Email Notifications
            "mailto://",
            "mailtos://",
            # Custom Notifications
            "form://",
            "forms://",
            "json://",
            "jsons://",
            "xml://",
            "xmls://",
            # Backward compatibility
            "telegram://",
        ]

        if not any(url.startswith(protocol) for protocol in supported_protocols):
            supported_services = [
                "HTTP/HTTPS (http://, https://)",
                "Email (mailto:)",
                "Slack (slack://)",
                "Discord (discord://)",
                "Telegram (tgram://)",
                "Pushover (pushover://)",
                "Gotify (gotify://)",
                "Zulip (zulip://)",
                "Matrix (matrix://)",
                "Rocket.Chat (rocketchat://)",
                "Mattermost (mattermost://)",
                "Microsoft Teams (teams://)",
                "Webex (webex://)",
                "Zoom (zoom://)",
                "Webhooks (webhook://)",
                "Generic (generic://)",
            ]
            msg = (
                "Invalid URL format. Must start with a supported protocol. "
                f"Examples: {', '.join(supported_services[:8])}..."
            )
            return False, msg

        return True, "Valid Apprise URL (basic validation)"


def add_apprise_url(url: str) -> tuple[bool, str]:
    """Add an Apprise URL to the list and update .env file."""
    with apprise_urls_lock:
        if url in current_apprise_urls:
            return False, "Apprise URL already exists"

        # Validate the URL
        is_valid, message = validate_apprise_url(url)
        if not is_valid:
            return False, message

        new_list = current_apprise_urls + [url]
        if update_env_file("APPRISE_URL", new_list):
            current_apprise_urls.append(url)
            # Add to the live Apprise object
            apobj.add(url)
            logging.info(f"Added Apprise URL: {url}")
            # Send notification about the addition
            total_urls = len(current_apprise_urls)
            msg = f"Apprise URL Added: {url} (Total: {total_urls} URLs)"
            send_notification(msg, apobj)
            return True, "Apprise URL added successfully"
        else:
            return False, "Failed to update .env file"


def remove_apprise_url(url: str) -> tuple[bool, str]:
    """Remove an Apprise URL from the list and update .env file."""
    with apprise_urls_lock:
        if url not in current_apprise_urls:
            return False, "Apprise URL not found"

        new_list = [u for u in current_apprise_urls if u != url]
        if update_env_file("APPRISE_URL", new_list):
            current_apprise_urls.remove(url)
            # Remove from the live Apprise object by recreating it
            apobj.clear()
            for remaining_url in current_apprise_urls:
                apobj.add(remaining_url)
            logging.info(f"Removed Apprise URL: {url}")
            # Send notification about the removal
            total_urls = len(current_apprise_urls)
            msg = f"Apprise URL Removed: {url} (Total: {total_urls} URLs)"
            send_notification(msg, apobj)
            return True, "Apprise URL removed successfully"
        else:
            return False, "Failed to update .env file"


# Graceful shutdown (cross-platform compatibility)
shutdown_event = asyncio.Event()


async def cleanup_http_session():
    """Clean up the shared HTTP session."""
    global _http_session
    if _http_session and not _http_session.closed:
        await _http_session.close()
        _http_session = None


def handle_shutdown_signal():
    logging.info("Shutdown signal received. Cleaning up...")
    shutdown_event.set()


# Only attach signal handlers on non-Windows
if os.name != "nt":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_shutdown_signal)
        except NotImplementedError:
            logging.warning(
                f"Signal handling is not implemented for {sig} on this platform."
            )

# FastAPI server
app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def home():
    uptime = datetime.now() - app_start_time
    uptime_str = str(uptime).split(".")[0]  # Remove microseconds

    # Get recent logs using thread-safe function
    recent_logs = get_recent_logs(20)  # Show last 20 entries

    # Build log HTML
    log_html = ""
    for entry in reversed(recent_logs):  # Show newest first
        level_color = {
            "INFO": "#28a745",
            "WARNING": "#ffc107",
            "ERROR": "#dc3545",
            "DEBUG": "#6c757d",
        }.get(entry["level"], "#000000")

        log_html += f"""
        <div style="margin: 5px 0; padding: 5px; border-left: 3px solid {level_color}; background-color: #f8f9fa;">
            <span style="color: #6c757d; font-size: 0.9em;">{entry['timestamp']}</span>
            <span style="color: {level_color}; font-weight: bold; margin-left: 10px;">[{entry['level']}]</span>
            <span style="margin-left: 10px;">{entry['message']}</span>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TestFlight Apprise Notifier - Status</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="refresh" content="30">
        <style>
            :root {{
                --bg-color: #f5f5f5;
                --container-bg: white;
                --card-bg: #f8f9fa;
                --text-color: #333;
                --text-secondary: #666;
                --border-color: #dee2e6;
                --header-border: #007bff;
                --success-color: #28a745;
                --danger-color: #dc3545;
                --warning-color: #ffc107;
                --info-color: #17a2b8;
                --shadow: rgba(0,0,0,0.1);
            }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 10px; 
                background-color: var(--bg-color);
                color: var(--text-color);
                transition: background-color 0.3s, color 0.3s;
            }}
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
                background-color: var(--container-bg); 
                padding: 15px; 
                border-radius: 8px; 
                box-shadow: 0 2px 4px var(--shadow);
                transition: background-color 0.3s, box-shadow 0.3s;
            }}
            .header {{ 
                text-align: center; 
                color: var(--text-color); 
                border-bottom: 2px solid var(--header-border); 
                padding-bottom: 10px; 
                margin-bottom: 20px;
                position: relative;
            }}
            .status-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; 
                margin-bottom: 30px;
            }}
            .status-card {{ 
                background-color: var(--card-bg); 
                padding: 15px; 
                border-radius: 6px; 
                border-left: 4px solid var(--success-color);
                transition: background-color 0.3s;
            }}
            .status-card h3 {{ 
                margin: 0 0 10px 0; 
                color: var(--text-color); 
                font-size: 1.1em;
            }}
            .status-card p {{
                margin: 5px 0;
                color: var(--text-secondary);
            }}
            .control-section {{
                margin: 30px 0;
                padding: 20px;
                background-color: var(--card-bg);
                border-radius: 8px;
                text-align: center;
                transition: background-color 0.3s;
            }}
            .control-section h2 {{
                margin: 0 0 20px 0;
                color: var(--text-color);
                font-size: 1.3em;
                font-weight: 600;
            }}
            .control-buttons {{
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
            }}
            .control-btn {{
                padding: 8px 16px;
                background-color: var(--success-color);
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 1em;
                font-weight: 600;
                margin: 0 5px;
                min-width: 140px;
                transition: background-color 0.2s;
            }}
            .control-btn:hover {{
                opacity: 0.9;
            }}
            .control-btn:disabled {{
                opacity: 0.6;
                cursor: not-allowed;
            }}
            .stop-btn {{
                background-color: var(--danger-color);
            }}
            .restart-btn {{
                background-color: var(--warning-color);
                color: #212529;
            }}
            .btn-icon {{
                font-size: 1.2em;
                display: inline-block;
            }}
            .btn-text {{
                font-weight: 600;
            }}
            .logs-section {{ 
                margin-top: 30px;
            }}
            .logs-header {{ 
                background-color: var(--card-bg); 
                color: var(--text-color);
                padding: 10px 15px; 
                margin: 0; 
                border-radius: 6px 6px 0 0;
            }}
            .logs-container {{ 
                max-height: 400px; 
                overflow-y: auto; 
                border: 1px solid var(--border-color); 
                border-top: none; 
                border-radius: 0 0 6px 6px; 
                padding: 10px;
                background-color: var(--container-bg);
            }}
            .refresh-info {{ 
                text-align: center; 
                color: var(--text-secondary); 
                font-size: 0.9em; 
                margin-top: 20px;
            }}
            .management-section {{ 
                margin: 30px 0; 
                padding: 20px; 
                background-color: var(--card-bg); 
                border-radius: 8px;
                transition: background-color 0.3s;
            }}
            .management-grid {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 20px;
            }}
            .management-card {{ 
                background-color: var(--container-bg); 
                padding: 15px; 
                border-radius: 6px; 
                border: 1px solid var(--border-color);
                transition: background-color 0.3s, border-color 0.3s;
            }}
            .management-card h3 {{
                margin: 0 0 15px 0;
                color: var(--text-color);
                font-size: 1.1em;
            }}
            .collapsible {{
                cursor: pointer;
                user-select: none;
                position: relative;
                padding-left: 20px;
            }}
            .collapsible:hover {{
                background-color: #f0f0f0;
            }}
            .collapsible::before {{
                content: "+";
                position: absolute;
                left: 0;
                top: 50%;
                transform: translateY(-50%);
                color: #666;
                font-weight: bold;
                font-size: 1.2em;
                transition: transform 0.2s ease;
                margin-right: 5px;
            }}
            .collapsible.expanded::before {{
                content: "−";
                transform: translateY(-50%);
            }}
            .collapsible-content {{
                display: none;
                padding-left: 20px;
            }}
            .collapsible-content.expanded {{
                display: block;
            }}
            @media (max-width: 768px) {{
                body {{
                    margin: 5px;
                }}
                .container {{
                    padding: 10px;
                }}
                .status-grid {{
                    grid-template-columns: 1fr;
                    gap: 15px;
                }}
                .management-section {{
                    margin: 20px 0;
                    padding: 15px;
                }}
                .logs-container {{
                    max-height: 300px;
                }}
                .control-section {{
                    padding: 15px;
                    margin: 20px 0;
                }}
                .control-buttons {{
                    gap: 10px;
                }}
                .control-btn {{
                    min-width: 120px;
                    padding: 8px 12px;
                    font-size: 0.9em;
                }}
            }}
            @media (max-width: 480px) {{
                .header {{
                    font-size: 1.5em;
                }}
                .status-card {{
                    padding: 12px;
                }}
                .management-card {{
                    padding: 12px;
                }}
                .collapsible {{
                    padding-left: 25px;
                    font-size: 1em;
                }}
                .control-section {{
                    padding: 15px;
                    margin: 15px 0;
                }}
                .control-section h2 {{
                    font-size: 1.1em;
                    margin-bottom: 10px;
                }}
                .control-buttons {{
                    flex-direction: column;
                    gap: 8px;
                }}
                .control-btn {{
                    min-width: 100%;
                    padding: 10px 16px;
                    font-size: 0.95em;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">🚀 TestFlight Apprise Notifier</h1>
            
            <div class="status-grid">
                <div class="status-card">
                    <h3>🟢 Bot Status</h3>
                    <p><strong>Status:</strong> Running</p>
                    <p><strong>Version:</strong> v{__version__}</p>
                    <p><strong>Uptime:</strong> {uptime_str}</p>
                </div>
                
                <div class="status-card">
                    <h3>📱 Monitoring</h3>
                    <p><strong>TestFlight IDs:</strong> <span id="id-count">{len(ID_LIST)}</span></p>
                    <p><strong>Apprise URLs:</strong> <span id="url-count">{len(APPRISE_URLS)}</span></p>
                    <p><strong>Check Interval:</strong> {SLEEP_TIME/1000:.1f}s</p>
                </div>
                
                <div class="status-card">
                    <h3>💓 Heartbeat</h3>
                    <p><strong>Interval:</strong> {HEARTBEAT_INTERVAL//3600}h</p>
                    <p><strong>Last Check:</strong> {format_datetime(datetime.now())}</p>
                </div>
            </div>
            
            <div class="control-section">
                <h2 style="color: var(--text-color); margin-bottom: 20px; text-align: center;">
                    ⚙️ Application & Notification Settings
                </h2>
                <div class="control-buttons">
                    <button class="control-btn stop-btn" onclick="stopApplication()">
                        🛑 Stop Application
                    </button>
                    <button class="control-btn restart-btn" onclick="restartApplication()">
                        🔄 Restart Application
                    </button>
                </div>
                
                <div class="management-grid" style="margin-top: 30px;">
                    <div class="management-card">
                        <h3 class="collapsible" onclick="toggleCard(this)">Add Apprise URL</h3>
                        <div class="collapsible-content">
                            <div style="margin-bottom: 10px;">
                                <input type="text" id="new-apprise-url" 
                                       placeholder="Enter Apprise URL (e.g., discord://...)" 
                                       style="padding: 8px; width: 100%; max-width: 300px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
                                <button onclick="validateAndAddUrl()" 
                                        style="padding: 8px 16px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 8px; width: 100%; max-width: 150px;">
                                    Validate & Add
                                </button>
                            </div>
                            <div id="add-url-status" style="margin-top: 10px; min-height: 20px;"></div>
                        </div>
                    </div>
                    
                    <div class="management-card">
                        <h3 class="collapsible" onclick="toggleCard(this)">Current Apprise URLs</h3>
                        <div class="collapsible-content">
                            <div id="current-urls" style="max-height: 200px; overflow-y: auto; border: 1px solid #dee2e6; padding: 10px; border-radius: 4px; background-color: #f8f9fa;">
                                Loading...
                            </div>
                            <button onclick="refreshUrls()" 
                                    style="margin-top: 10px; padding: 6px 12px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                🔄 Refresh
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <h2 style="color: var(--text-color); margin-bottom: 20px;">
                🔧 TestFlight ID Management
            </h2>
                
                <div class="management-grid">
                    <div class="management-card">
                        <h3 class="collapsible" onclick="toggleCard(this)">Add TestFlight ID</h3>
                        <div class="collapsible-content">
                            <div style="margin-bottom: 10px;">
                                <input type="text" id="new-tf-id" placeholder="Enter TestFlight ID" 
                                       style="padding: 8px; width: 100%; max-width: 250px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
                                <button onclick="validateAndAddId()" 
                                        style="padding: 8px 16px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 8px; width: 100%; max-width: 150px;">
                                    Validate & Add
                                </button>
                            </div>
                            <div id="add-status" style="margin-top: 10px; min-height: 20px;"></div>
                        </div>
                    </div>
                    
                    <div class="management-card">
                        <h3 class="collapsible" onclick="toggleCard(this)">Current TestFlight IDs</h3>
                        <div class="collapsible-content">
                            <div id="current-ids" style="max-height: 200px; overflow-y: auto; border: 1px solid #dee2e6; padding: 10px; border-radius: 4px; background-color: #f8f9fa;">
                                Loading...
                            </div>
                            <button onclick="refreshIds()" 
                                    style="margin-top: 10px; padding: 6px 12px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                🔄 Refresh
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="logs-section">
                <h3 class="logs-header">📜 Recent Activity (Last 20 entries)</h3>
                <div class="logs-container">
                    {log_html if log_html else '<div style="text-align: center; color: #6c757d; padding: 20px;">No log entries yet...</div>'}
                </div>
            </div>
            
            <div class="refresh-info">
                🔄 Page auto-refreshes every 30 seconds | Last updated: {format_datetime(datetime.now())}
            </div>
        </div>
        
        <script>
            function toggleCard(header) {{
                const content = header.nextElementSibling;
                const isExpanded = content.classList.contains('expanded');
                
                // Toggle the content visibility
                content.classList.toggle('expanded');
                
                // Toggle the arrow rotation
                header.classList.toggle('expanded');
                
                // Optionally collapse other cards when one is expanded
                if (!isExpanded) {{
                    // Close other cards
                    document.querySelectorAll('.collapsible-content.expanded').forEach(otherContent => {{
                        if (otherContent !== content) {{
                            otherContent.classList.remove('expanded');
                            otherContent.previousElementSibling.classList.remove('expanded');
                        }}
                    }});
                }}
            }}
            
            async function refreshIds() {{
                try {{
                    const response = await fetch('/api/testflight-ids/details');
                    const data = await response.json();
                    displayIds(data.testflight_ids);
                    document.getElementById('id-count').textContent = data.testflight_ids.length;
                }} catch (error) {{
                    console.error('Error refreshing IDs:', error);
                }}
            }}
            
            function displayIds(ids) {{
                const container = document.getElementById('current-ids');
                if (ids.length === 0) {{
                    container.innerHTML = '<em>No TestFlight IDs configured</em>';
                    return;
                }}
                
                container.innerHTML = ids.map(item => {{
                    const displayName = item.display_name || item.id;
                    const isAppName = item.app_name && item.app_name !== item.id;
                    const iconHtml = item.icon_url ? 
                        `<img src="${{item.icon_url}}" style="width: 20px; height: 20px; border-radius: 4px; margin-right: 8px; vertical-align: middle;" alt="App Icon">` : 
                        '📱 ';
                    
                    return `<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #eee;">
                        <div style="display: flex; align-items: center; flex-grow: 1;">
                            ${{iconHtml}}
                            <div>
                                <div style="font-weight: ${{isAppName ? 'bold' : 'normal'}};">${{displayName}}</div>
                                ${{isAppName ? `<div style="font-size: 0.8em; color: #666;">${{item.id}}</div>` : ''}}
                            </div>
                        </div>
                        <button onclick="removeId('${{item.id}}')" 
                                style="padding: 8px 16px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em;">
                            ❌ Remove
                        </button>
                    </div>`;
                }}).join('');
            }}
            
            async function validateAndAddId() {{
                const tfId = document.getElementById('new-tf-id').value.trim();
                const statusDiv = document.getElementById('add-status');
                
                if (!tfId) {{
                    statusDiv.innerHTML = '<span style="color: #dc3545;">Please enter a TestFlight ID</span>';
                    return;
                }}
                
                statusDiv.innerHTML = '<span style="color: #007bff;">Validating...</span>';
                
                try {{
                    // First validate
                    const validateResponse = await fetch('/api/testflight-ids/validate', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ id: tfId }})
                    }});
                    
                    const validateData = await validateResponse.json();
                    
                    if (!validateData.valid) {{
                        statusDiv.innerHTML = `<span style="color: #dc3545;">${{validateData.message}}</span>`;
                        return;
                    }}
                    
                    // Show validation success with app name if available
                    let validationMessage = 'Valid TestFlight ID';
                    if (validateData.app_name && validateData.app_name !== tfId) {{
                        const iconHtml = validateData.icon_url ? 
                            `<img src="${{validateData.icon_url}}" style="width: 16px; height: 16px; border-radius: 3px; margin-right: 5px; vertical-align: middle;" alt="App Icon">` : 
                            '📱 ';
                        validationMessage = `${{iconHtml}}Found: <strong>${{validateData.app_name}}</strong>`;
                    }}
                    statusDiv.innerHTML = `<span style="color: #28a745;">${{validationMessage}}</span>`;
                    
                    // Add small delay to show the validation result before adding
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // If valid, add it
                    statusDiv.innerHTML = '<span style="color: #007bff;">Adding...</span>';
                    
                    const addResponse = await fetch('/api/testflight-ids', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ id: tfId }})
                    }});
                    
                    const addData = await addResponse.json();
                    
                    if (addResponse.ok) {{
                        statusDiv.innerHTML = `<span style="color: #28a745;">${{addData.message}}</span>`;
                        document.getElementById('new-tf-id').value = '';
                        displayIds(addData.testflight_ids);
                        document.getElementById('id-count').textContent = addData.testflight_ids.length;
                    }} else {{
                        statusDiv.innerHTML = `<span style="color: #dc3545;">${{addData.detail || 'Failed to add ID'}}</span>`;
                    }}
                }} catch (error) {{
                    statusDiv.innerHTML = `<span style="color: #dc3545;">Error: ${{error.message}}</span>`;
                }}
            }}
            
            async function removeId(tfId) {{
                if (!confirm(`Are you sure you want to remove TestFlight ID "${{tfId}}"?`)) {{
                    return;
                }}
                
                try {{
                    const response = await fetch(`/api/testflight-ids/${{tfId}}`, {{
                        method: 'DELETE'
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        displayIds(data.testflight_ids);
                        document.getElementById('id-count').textContent = data.testflight_ids.length;
                        alert(data.message);
                    }} else {{
                        alert(`Failed to remove ID: ${{data.detail || 'Unknown error'}}`);
                    }}
                }} catch (error) {{
                    alert(`Error removing ID: ${{error.message}}`);
                }}
            }}
            
            async function refreshUrls() {{
                try {{
                    const response = await fetch('/api/apprise-urls');
                    const data = await response.json();
                    displayUrls(data.apprise_urls);
                }} catch (error) {{
                    console.error('Error refreshing URLs:', error);
                }}
            }}
            
            function displayUrls(urls) {{
                const container = document.getElementById('current-urls');
                if (urls.length === 0) {{
                    container.innerHTML = '<em>No Apprise URLs configured</em>';
                    return;
                }}
                
                container.innerHTML = urls.map(url => {{
                    // Extract service type from URL for icon
                    let icon = '📢';
                    if (url.includes('discord://')) icon = '💬';
                    else if (url.includes('slack://')) icon = '💼';
                    else if (url.includes('telegram://')) icon = '✈️';
                    else if (url.includes('pushover://')) icon = '📱';
                    else if (url.includes('gotify://')) icon = '🔔';
                    else if (url.includes('mailto:')) icon = '📧';
                    else if (url.includes('http://') || url.includes('https://')) icon = '🌐';
                    
                    // Mask sensitive parts of the URL for display
                    let displayUrl = url;
                    try {{
                        const urlObj = new URL(url);
                        if (urlObj.username || urlObj.password) {{
                            displayUrl = url.replace(urlObj.username + ':' + urlObj.password, '***:***');
                        }}
                        // Hide query parameters for security
                        displayUrl = displayUrl.split('?')[0];
                    }} catch (e) {{
                        // If URL parsing fails, just show a masked version
                        displayUrl = url.substring(0, 20) + '...';
                    }}
                    
                    return `<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #eee;">
                        <div style="display: flex; align-items: center; flex-grow: 1;">
                            <span style="font-size: 1.2em; margin-right: 8px;">${{icon}}</span>
                            <span style="font-family: monospace; font-size: 0.9em;">${{displayUrl}}</span>
                        </div>
                        <button onclick="removeUrl('${{encodeURIComponent(url)}}')" 
                                style="padding: 8px 16px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em;">
                            ❌ Remove
                        </button>
                    </div>`;
                }}).join('');
            }}
            
            async function validateAndAddUrl() {{
                const url = document.getElementById('new-apprise-url').value.trim();
                const statusDiv = document.getElementById('add-url-status');
                
                if (!url) {{
                    statusDiv.innerHTML = '<span style="color: #dc3545;">Please enter an Apprise URL</span>';
                    return;
                }}
                
                statusDiv.innerHTML = '<span style="color: #007bff;">Validating...</span>';
                
                try {{
                    // First validate
                    const validateResponse = await fetch('/api/apprise-urls/validate', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ url: url }})
                    }});
                    
                    const validateData = await validateResponse.json();
                    
                    if (!validateData.valid) {{
                        statusDiv.innerHTML = `<span style="color: #dc3545;">${{validateData.message}}</span>`;
                        return;
                    }}
                    
                    // Show validation success
                    statusDiv.innerHTML = `<span style="color: #28a745;">${{validateData.message}}</span>`;
                    
                    // Add small delay to show the validation result before adding
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // If valid, add it
                    statusDiv.innerHTML = '<span style="color: #007bff;">Adding...</span>';
                    
                    const addResponse = await fetch('/api/apprise-urls', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ url: url }})
                    }});
                    
                    const addData = await addResponse.json();
                    
                    if (addResponse.ok) {{
                        statusDiv.innerHTML = `<span style="color: #28a745;">${{addData.message}}</span>`;
                        document.getElementById('new-apprise-url').value = '';
                        displayUrls(addData.apprise_urls);
                        document.getElementById('url-count').textContent = addData.apprise_urls.length;
                    }} else {{
                        statusDiv.innerHTML = `<span style="color: #dc3545;">${{addData.detail || 'Failed to add URL'}}</span>`;
                    }}
                }} catch (error) {{
                    statusDiv.innerHTML = `<span style="color: #dc3545;">Error: ${{error.message}}</span>`;
                }}
            }}
            
            async function removeUrl(encodedUrl) {{
                const url = decodeURIComponent(encodedUrl);
                if (!confirm(`Are you sure you want to remove this Apprise URL?`)) {{
                    return;
                }}
                
                try {{
                    const response = await fetch(`/api/apprise-urls/${{encodedUrl}}`, {{
                        method: 'DELETE'
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        displayUrls(data.apprise_urls);
                        document.getElementById('url-count').textContent = data.apprise_urls.length;
                        alert(data.message);
                    }} else {{
                        alert(`Failed to remove URL: ${{data.detail || 'Unknown error'}}`);
                    }}
                }} catch (error) {{
                    alert(`Error removing URL: ${{error.message}}`);
                }}
            }}
            
            // Load IDs on page load
            document.addEventListener('DOMContentLoaded', function() {{
                refreshIds();
                refreshUrls();
                // Initialize collapsible sections - expand by default
                document.querySelectorAll('.collapsible-content').forEach(content => {{
                    content.classList.add('expanded');
                }});
                document.querySelectorAll('.collapsible').forEach(header => {{
                    header.classList.add('expanded');
                }});
            }});
            
            // Allow Enter key to submit
            document.getElementById('new-tf-id').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    validateAndAddId();
                }}
            }});
            
            async function stopApplication() {{
                if (!confirm('Are you sure you want to stop the TestFlight Apprise Notifier? This will shut down the application.')) {{
                    return;
                }}
                
                try {{
                    const response = await fetch('/api/control/stop', {{
                        method: 'POST'
                    }});
                    
                    if (response.ok) {{
                        alert('Application is shutting down...');
                        // Disable buttons
                        document.querySelector('.stop-btn').disabled = true;
                        document.querySelector('.restart-btn').disabled = true;
                        // Show shutdown message
                        document.querySelector('.container').innerHTML = `
                            <div style="text-align: center; padding: 50px;">
                                <h2>🛑 Application Stopped</h2>
                                <p>The TestFlight Apprise Notifier has been shut down.</p>
                                <p>To restart, run the application again from the command line.</p>
                            </div>
                        `;
                    }} else {{
                        alert('Failed to stop application');
                    }}
                }} catch (error) {{
                    alert('Error stopping application: ' + error.message);
                }}
            }}
            
            async function restartApplication() {{
                if (!confirm('Are you sure you want to restart the TestFlight Apprise Notifier? This will reload the application with any code changes.')) {{
                    return;
                }}
                
                try {{
                    const response = await fetch('/api/control/restart', {{
                        method: 'POST'
                    }});
                    
                    if (response.ok) {{
                        alert('Application is restarting...');
                        // Disable buttons
                        document.querySelector('.stop-btn').disabled = true;
                        document.querySelector('.restart-btn').disabled = true;
                        // Show restart message
                        document.querySelector('.container').innerHTML = `
                            <div style="text-align: center; padding: 50px;">
                                <h2>🔄 Application Restarting</h2>
                                <p>The TestFlight Apprise Notifier is restarting...</p>
                                <p>Please wait a moment and refresh the page.</p>
                            </div>
                        `;
                    }} else {{
                        alert('Failed to restart application');
                    }}
                }} catch (error) {{
                    alert('Error restarting application: ' + error.message);
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    current_ids = get_current_id_list()
    circuit_breaker_status = {
        url: failures for url, (failures, _) in _request_failures.items()
    }

    return {
        "status": "healthy",
        "version": __version__,
        "uptime_seconds": int((datetime.now() - app_start_time).total_seconds()),
        "monitored_ids": len(current_ids),
        "cache_stats": {
            "app_names": len(app_name_cache.cache),
            "app_icons": len(app_icon_cache.cache),
        },
        "circuit_breaker": {
            "open_circuits": len(
                [
                    url
                    for url in circuit_breaker_status.keys()
                    if is_circuit_breaker_open(url)
                ]
            ),
            "total_tracked": len(circuit_breaker_status),
        },
        "http_session": (
            "active" if _http_session and not _http_session.closed else "inactive"
        ),
        "timestamp": format_datetime(datetime.now()),
    }


@app.get("/api/logs")
async def api_logs(limit: int = 50):
    """API endpoint for recent logs in JSON format with input validation"""
    # Input validation for limit parameter
    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be at least 1")
    if limit > 1000:
        raise HTTPException(
            status_code=400, detail="Limit cannot exceed 1000 for performance reasons"
        )

    # Get logs using thread-safe function with efficient slicing
    recent_logs = get_recent_logs(limit)

    with log_entries_lock:
        total_entries = len(log_entries)

    return {
        "logs": list(reversed(recent_logs)),
        "total_entries": total_entries,
        "limit": limit,
    }


@app.get("/api/testflight-ids")
async def get_testflight_ids():
    """Get current list of TestFlight IDs."""
    return {"testflight_ids": get_current_id_list()}


@app.get("/api/testflight-ids/details")
async def get_testflight_ids_details():
    """Get detailed information for all TestFlight IDs."""
    current_ids = get_current_id_list()
    details = []

    for tf_id in current_ids:
        try:
            # Get app name (with caching)
            app_name = await get_app_name(TESTFLIGHT_URL, tf_id)

            # Get app icon URL (with caching)
            icon_url = await get_app_icon(TESTFLIGHT_URL, tf_id)

            details.append(
                {
                    "id": tf_id,
                    "app_name": app_name if app_name != tf_id else None,
                    "display_name": app_name,
                    "icon_url": icon_url,
                }
            )
        except Exception as e:
            logging.warning(f"Failed to get details for TestFlight ID {tf_id}: {e}")
            # Fallback to just the ID
            details.append(
                {"id": tf_id, "app_name": None, "display_name": tf_id, "icon_url": None}
            )

    return {"testflight_ids": details}


@app.post("/api/testflight-ids/validate")
async def validate_id(request: Request):
    """Validate a TestFlight ID."""
    data = await request.json()
    tf_id = data.get("id", "").strip()

    if not tf_id:
        raise HTTPException(status_code=400, detail="TestFlight ID is required")

    is_valid, message = await validate_testflight_id(tf_id)

    # If valid, also get the app name and icon for display
    app_name = None
    icon_url = None
    if is_valid:
        try:
            app_name = await get_app_name(TESTFLIGHT_URL, tf_id)
            icon_url = await get_app_icon(TESTFLIGHT_URL, tf_id)
        except Exception as e:
            logging.warning(
                f"Failed to get app details during validation for {tf_id}: {e}"
            )

    return {
        "valid": is_valid,
        "message": message,
        "app_name": app_name,
        "icon_url": icon_url,
    }


@app.post("/api/testflight-ids")
async def add_id(request: Request):
    """Add a new TestFlight ID."""
    data = await request.json()
    tf_id = data.get("id", "").strip()

    if not tf_id:
        raise HTTPException(status_code=400, detail="TestFlight ID is required")

    # Validate first
    is_valid, message = await validate_testflight_id(tf_id)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    # Add to list
    success, message = add_testflight_id(tf_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"message": message, "testflight_ids": get_current_id_list()}


@app.delete("/api/testflight-ids/{tf_id}")
async def remove_id(tf_id: str):
    """Remove a TestFlight ID."""
    success, message = remove_testflight_id(tf_id)
    if not success:
        raise HTTPException(status_code=404, detail=message)

    return {"message": message, "testflight_ids": get_current_id_list()}


@app.get("/api/apprise-urls")
async def get_apprise_urls():
    """Get current list of Apprise URLs."""
    return {"apprise_urls": get_current_apprise_urls()}


@app.post("/api/apprise-urls/validate")
async def validate_url(request: Request):
    """Validate an Apprise URL."""
    data = await request.json()
    url = data.get("url", "").strip()

    if not url:
        raise HTTPException(status_code=400, detail="Apprise URL is required")

    is_valid, message = validate_apprise_url(url)

    return {
        "valid": is_valid,
        "message": message,
    }


@app.post("/api/apprise-urls")
async def add_url(request: Request):
    """Add a new Apprise URL."""
    data = await request.json()
    url = data.get("url", "").strip()

    if not url:
        raise HTTPException(status_code=400, detail="Apprise URL is required")

    # Add to list
    success, message = add_apprise_url(url)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"message": message, "apprise_urls": get_current_apprise_urls()}


@app.delete("/api/apprise-urls/{url:path}")
async def remove_url(url: str):
    """Remove an Apprise URL."""
    # URL decode the path parameter since it might contain special characters
    import urllib.parse

    decoded_url = urllib.parse.unquote(url)

    success, message = remove_apprise_url(decoded_url)
    if not success:
        raise HTTPException(status_code=404, detail=message)

    return {"message": message, "apprise_urls": get_current_apprise_urls()}


@app.post("/api/control/stop")
async def stop_application():
    """Stop the application gracefully."""
    logging.info("Stop command received via web interface")
    # Send notification about the stop
    try:
        msg = "🛑 TestFlight Apprise Notifier stopped via web interface"
        send_notification(msg, apobj)
    except Exception:
        pass  # Ignore notification errors during shutdown

    # Trigger graceful shutdown
    handle_shutdown_signal()
    return {"message": "Application is shutting down..."}


@app.post("/api/control/restart")
async def restart_application():
    """Restart the application."""
    logging.info("Restart command received via web interface")

    # Send notification about the restart
    try:
        msg = "🔄 TestFlight Apprise Notifier restarting via web interface"
        send_notification(msg, apobj)
    except Exception:
        pass  # Ignore notification errors during restart

    # Get the current Python executable and script path
    import sys
    import subprocess
    import os

    python_executable = sys.executable
    script_path = os.path.abspath(sys.argv[0])

    try:
        # Start a new instance of the application
        subprocess.Popen(
            [python_executable, script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

        logging.info("New application instance started, shutting down current instance")

        # Trigger graceful shutdown of current instance
        handle_shutdown_signal()

        return {"message": "Application is restarting..."}

    except Exception as e:
        logging.error(f"Failed to restart application: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart: {str(e)}")


async def fetch_testflight_status(session, tf_id):
    """Fetch and check TestFlight status."""
    testflight_url = format_link(TESTFLIGHT_URL, tf_id)
    try:
        async with session.get(
            testflight_url, headers={"Accept-Language": "en-us"}
        ) as response:
            if response.status != 200:
                logging.warning(
                    "%s - %s - Not Found. URL: %s",
                    response.status,
                    tf_id,
                    testflight_url,
                )
                return

            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            status_text = soup.select_one(".beta-status span")
            status_text = status_text.text.strip() if status_text else ""

            # Get app name using the cached function
            app_name = await get_app_name(TESTFLIGHT_URL, tf_id)

            if status_text in [NOT_OPEN_TEXT, FULL_TEXT]:
                logging.info(f"{response.status} - {app_name} - {status_text}")

                # For full or expired apps, send notification with app icon
                if status_text == FULL_TEXT:
                    notify_msg = await format_notification_link(TESTFLIGHT_URL, tf_id)
                    icon_url = await get_app_icon(TESTFLIGHT_URL, tf_id)
                    # Use stock TestFlight icon if app icon is unavailable
                    if not icon_url or icon_url == tf_id:
                        # Stock TestFlight icon URL
                        base_url = "https://developer.apple.com/assets/elements/icons"
                        icon_url = f"{base_url}/testflight/testflight-64x64_2x.png"
                    await send_notification_async(notify_msg, apobj)
                    logging.info(f"Sent notification for full beta: {app_name}")
                return

            notify_msg = await format_notification_link(TESTFLIGHT_URL, tf_id)
            icon_url = await get_app_icon(TESTFLIGHT_URL, tf_id)
            await send_notification_async(notify_msg, apobj)
            logging.info(f"{response.status} - {app_name} - {status_text}")
    except aiohttp.ClientResponseError as e:
        logging.error(f"HTTP error fetching {tf_id}: {e}")
    except aiohttp.ClientError as e:
        logging.error(f"Network error fetching {tf_id}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching {tf_id}: {e}")


async def watch():
    """Check all TestFlight links."""
    current_ids = get_current_id_list()
    session = await get_http_session()
    tasks = [fetch_testflight_status(session, tf_id) for tf_id in current_ids]
    await asyncio.gather(*tasks)


async def heartbeat():
    """Send periodic heartbeat notifications."""
    while True:
        current_time = format_datetime(datetime.now())
        message = f"Heartbeat - {current_time}"
        send_notification(message, apobj)
        print_green(message)
        await asyncio.sleep(HEARTBEAT_INTERVAL)


async def start_watching():
    """Continuously check TestFlight links."""
    # Add small delay to ensure server starts first
    await asyncio.sleep(2)
    while not shutdown_event.is_set():
        await watch()
        await asyncio.sleep(SLEEP_TIME / 1000)  # Convert ms to seconds


async def start_fastapi():
    """Start FastAPI server as an async task."""
    try:
        default_host = os.getenv("FASTAPI_HOST", "0.0.0.0")
        default_port = int(os.getenv("FASTAPI_PORT", random.randint(8000, 9000)))

        logging.info(f"Starting FastAPI server on {default_host}:{default_port}")

        config = uvicorn.Config(
            app,
            host=default_host,
            port=default_port,
            log_level="info",
            access_log=False,  # Disable access logs to prevent console spam
        )
        server = uvicorn.Server(config)
        await server.serve()
    except asyncio.CancelledError:
        logging.info("FastAPI server cancelled during shutdown")
        raise  # Re-raise to be handled by the task system
    except Exception as e:
        logging.error(f"Failed to start FastAPI server: {e}")
        raise


def main():
    """Main function to start all tasks."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logging.info("Shutdown initiated by user (CTRL+C).")
        shutdown_event.set()
    except Exception as e:
        logging.error(f"Unexpected error during shutdown: {e}")
    finally:
        logging.info("Application has stopped.")


async def async_main():
    """Run async tasks in the main event loop."""
    tasks = []
    try:
        logging.info("Starting TestFlight Apprise Notifier v%s", __version__)
        logging.info("All services starting...")

        # Create tasks
        watching_task = asyncio.create_task(start_watching())
        heartbeat_task = asyncio.create_task(heartbeat())
        fastapi_task = asyncio.create_task(start_fastapi())
        shutdown_task = asyncio.create_task(shutdown_event.wait())

        tasks = [watching_task, heartbeat_task, fastapi_task, shutdown_task]

        # Wait for any task to complete (shutdown event or error)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        logging.info("Shutdown initiated, cancelling tasks...")

        # Cancel all pending tasks
        for task in pending:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete and handle exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any exceptions that occurred during shutdown
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_name = (
                    tasks[i].get_name()
                    if hasattr(tasks[i], "get_name")
                    else f"Task-{i+1}"
                )
                if isinstance(result, asyncio.CancelledError):
                    logging.debug(f"{task_name} was cancelled during shutdown")
                elif isinstance(result, SystemExit) and result.code == 1:
                    logging.debug(
                        f"{task_name} (uvicorn) exited normally during shutdown"
                    )
                else:
                    logging.warning(f"{task_name} finished with exception: {result}")

    except asyncio.CancelledError:
        logging.info("Async tasks cancelled during shutdown.")
    except Exception as e:
        logging.error(f"Error in async main: {e}")
    finally:
        # Clean up HTTP session
        await cleanup_http_session()
        logging.info("HTTP session cleaned up.")
        logging.info("Async main loop has exited.")


if __name__ == "__main__":
    main()
