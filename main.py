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
from contextlib import asynccontextmanager
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
from utils.testflight import (
    check_testflight_status,
    TestFlightStatus,
    is_status_available,
    enable_status_cache,
)

# Enable status caching with 5-minute TTL for improved performance
enable_status_cache(ttl_seconds=300)

# Circuit breaker for external requests
_request_failures = {}
_circuit_breaker_threshold = 5
_circuit_breaker_timeout = 300  # 5 minutes

# Global HTTP session and lock
_http_session = None
_session_lock = threading.Lock()

# Status tracking for change notifications
_previous_status = {}  # tf_id -> TestFlightStatus
_status_lock = threading.Lock()


class MetricsCollector:
    """
    Collect and track metrics for TestFlight status checks.

    Tracks total checks, successes, failures, and status counts.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.total_checks = 0
        self.successful_checks = 0
        self.failed_checks = 0
        self.status_counts = {
            "open": 0,
            "full": 0,
            "closed": 0,
            "unknown": 0,
            "error": 0,
        }
        self.start_time = time.time()
        self._lock = threading.Lock()

    def record_check(self, status: TestFlightStatus, success: bool = True):
        """
        Record a status check.

        Args:
            status: The TestFlightStatus result
            success: Whether the check was successful
        """
        with self._lock:
            self.total_checks += 1
            if success:
                self.successful_checks += 1
                status_key = status.value.lower()
                if status_key in self.status_counts:
                    self.status_counts[status_key] += 1
            else:
                self.failed_checks += 1
                self.status_counts["error"] += 1

    def get_stats(self):
        """
        Get current statistics.

        Returns:
            dict: Statistics dictionary with all metrics
        """
        with self._lock:
            uptime = time.time() - self.start_time
            return {
                "total_checks": self.total_checks,
                "successful_checks": self.successful_checks,
                "failed_checks": self.failed_checks,
                "status_counts": self.status_counts.copy(),
                "uptime_seconds": uptime,
                "checks_per_minute": (
                    (self.total_checks / uptime * 60) if uptime > 0 else 0
                ),
            }

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self.total_checks = 0
            self.successful_checks = 0
            self.failed_checks = 0
            self.status_counts = {
                "open": 0,
                "full": 0,
                "closed": 0,
                "unknown": 0,
                "error": 0,
            }
            self.start_time = time.time()


# Global metrics collector
_metrics = MetricsCollector()

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
__version__ = "1.0.5d"


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

# Parse ID_LIST (supporting multi-line format)
id_list_raw_value = get_multiline_env_value("ID_LIST")
id_list_raw = [
    tf_id.strip().rstrip(",")
    for tf_id in id_list_raw_value.replace("\n", ",").split(",")
    if tf_id.strip()
]

SLEEP_TIME = int(os.getenv("INTERVAL_CHECK", "10000"))  # in ms
TITLE_REGEX = re.compile(r"Join the (.+) beta - TestFlight - Apple")

# Parse Apprise URLs (supporting multi-line format)
apprise_url_raw = get_multiline_env_value("APPRISE_URL")
apprise_urls_raw = [
    url.strip().rstrip(",")
    for url in apprise_url_raw.replace("\n", ",").split(",")
    if url.strip()
]

# Heartbeat interval (default: 6 hours)
# Can be configured via HEARTBEAT_INTERVAL environment variable (in hours)
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "6")) * 60 * 60  # Convert hours to seconds

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


# Custom uvicorn log config that preserves our formatting
def get_uvicorn_log_config():
    """
    Create a uvicorn log config that uses our existing logging setup.
    
    This prevents uvicorn from reconfiguring logging while still allowing
    it to log properly through our configured handlers.
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,  # Keep our handlers!
        "formatters": {
            "default": {
                "format": format_str,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
        },
    }


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

        # Find and update the key line, removing old continuation lines
        updated = False
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith(f"{key}="):
                # Found the key, remove this line and all continuation lines
                lines.pop(i)
                
                # Remove continuation lines (lines that don't start with a key)
                while i < len(lines):
                    next_line = lines[i].strip()
                    # Stop if we hit another key or empty line
                    if not next_line or next_line.startswith("#") or "=" in next_line:
                        break
                    # This is a continuation line, remove it
                    lines.pop(i)
                
                # Insert new values at this position
                if new_values:
                    # Write first value on the key line
                    lines.insert(i, f"{key}={new_values[0]},\n")
                    # Write remaining values as continuation lines
                    for j, value in enumerate(new_values[1:], 1):
                        lines.insert(i + j, f"{value},\n")
                else:
                    # Empty value
                    lines.insert(i, f"{key}=\n")
                
                updated = True
                break
            i += 1

        if not updated:
            # Add the key if it doesn't exist
            if new_values:
                lines.append(f"{key}={new_values[0]},\n")
                # Add additional lines
                for value in new_values[1:]:
                    lines.append(f"{value},\n")
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


def validate_testflight_id_format(tf_id):
    """
    Validate TestFlight ID format.

    Args:
        tf_id: The TestFlight ID to validate

    Returns:
        tuple: (is_valid, message)
    """
    if not tf_id or not tf_id.strip():
        return False, "TestFlight ID cannot be empty"

    tf_id = tf_id.strip()

    # TestFlight IDs are typically 8-12 alphanumeric characters
    import re

    if not re.match(r"^[a-zA-Z0-9]{8,12}$", tf_id):
        return False, (
            "Invalid TestFlight ID format. " "ID must be 8-12 alphanumeric characters"
        )

    return True, "Valid format"


async def validate_testflight_id(tf_id):
    """Validate if a TestFlight ID exists and is accessible."""
    # First check format
    is_valid_format, format_message = validate_testflight_id_format(tf_id)
    if not is_valid_format:
        return False, format_message

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


# FastAPI lifespan context manager for proper startup/shutdown handling
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage FastAPI application lifespan.
    
    Handles startup and shutdown events gracefully, including proper
    exception handling for cancellation during shutdown/restart.
    """
    # Startup
    logging.info("FastAPI application starting up...")
    try:
        yield
    except asyncio.CancelledError:
        # This is expected during graceful shutdown/restart
        logging.info("FastAPI lifespan cancelled during shutdown/restart")
    finally:
        # Shutdown
        logging.info("FastAPI application shutting down...")
        await cleanup_http_session()


# FastAPI server
app = FastAPI(lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def home():
    """
    Render the web interface with enhanced UI features:
    - Dark mode toggle with localStorage persistence
    - Confirmation dialogs for destructive actions
    - Loading states on all async operations
    - Toast notifications instead of alerts
    - Live metrics dashboard
    - Test notification button
    - Copy-to-clipboard buttons
    - Custom favicon
    """
    # Get current configuration
    testflight_ids = get_current_id_list()
    apprise_urls = get_current_apprise_urls()
    check_interval = SLEEP_TIME / 1000  # Convert ms to seconds
    
    # Get version
    version = __version__
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TestFlight Notifier</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚀</text></svg>">
    <style>
        :root {{
            --bg-primary: #f5f5f5;
            --bg-secondary: white;
            --bg-tertiary: #f9f9f9;
            --bg-code: #1e1e1e;
            --text-primary: #333;
            --text-secondary: #666;
            --text-code: #d4d4d4;
            --border-color: #ddd;
            --shadow: rgba(0,0,0,0.1);
            --accent-primary: #4CAF50;
            --accent-danger: #f44336;
            --accent-warning: #FF9800;
            --accent-info: #2196F3;
            --log-info: #4FC3F7;
            --log-success: #81C784;
            --log-warning: #FFB74D;
            --log-error: #E57373;
        }}
        
        [data-theme="dark"] {{
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #383838;
            --bg-code: #0d0d0d;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --text-code: #d4d4d4;
            --border-color: #444;
            --shadow: rgba(0,0,0,0.3);
            --accent-primary: #66BB6A;
            --accent-danger: #EF5350;
            --accent-warning: #FFA726;
            --accent-info: #42A5F5;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            padding: 20px;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px var(--shadow);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .header-left {{
            flex: 1;
        }}
        
        h1 {{
            color: var(--text-primary);
            margin-bottom: 10px;
        }}
        
        .version {{
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        
        .header-right {{
            display: flex;
            gap: 15px;
            align-items: center;
        }}
        
        .theme-toggle {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 1.1em;
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.05);
            box-shadow: 0 2px 8px var(--shadow);
        }}
        
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: 500;
        }}
        
        .status.running {{
            background-color: var(--accent-primary);
            color: white;
        }}
        
        .status.stopped {{
            background-color: var(--accent-danger);
            color: white;
        }}
        
        .card {{
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px var(--shadow);
        }}
        
        .card h2 {{
            color: var(--text-primary);
            margin-bottom: 15px;
            border-bottom: 2px solid var(--accent-primary);
            padding-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .copy-btn {{
            background: var(--accent-info);
            color: white;
            border: none;
            padding: 5px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.2s;
        }}
        
        .copy-btn:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
        }}
        
        .control-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        
        button {{
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
            position: relative;
        }}
        
        button:hover:not(:disabled) {{
            opacity: 0.9;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px var(--shadow);
        }}
        
        button:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
        }}
        
        button.loading {{
            pointer-events: none;
        }}
        
        button.loading::after {{
            content: '';
            position: absolute;
            width: 16px;
            height: 16px;
            top: 50%;
            left: 50%;
            margin-left: -8px;
            margin-top: -8px;
            border: 2px solid transparent;
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .btn-start {{
            background-color: var(--accent-primary);
            color: white;
        }}
        
        .btn-stop {{
            background-color: var(--accent-danger);
            color: white;
        }}
        
        .btn-restart {{
            background-color: var(--accent-warning);
            color: white;
        }}
        
        .btn-refresh {{
            background-color: var(--accent-info);
            color: white;
        }}
        
        .btn-test {{
            background-color: #9C27B0;
            color: white;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .info-item {{
            background: var(--bg-tertiary);
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid var(--accent-primary);
            transition: transform 0.2s;
        }}
        
        .info-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px var(--shadow);
        }}
        
        .info-item label {{
            display: block;
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        
        .info-item .value {{
            font-size: 1.2em;
            font-weight: 500;
            color: var(--text-primary);
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, var(--accent-info) 0%, #1976D2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px var(--shadow);
            transition: transform 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 6px 12px var(--shadow);
        }}
        
        .metric-card.success {{
            background: linear-gradient(135deg, var(--accent-primary) 0%, #388E3C 100%);
        }}
        
        .metric-card.warning {{
            background: linear-gradient(135deg, var(--accent-warning) 0%, #F57C00 100%);
        }}
        
        .metric-card.danger {{
            background: linear-gradient(135deg, var(--accent-danger) 0%, #D32F2F 100%);
        }}
        
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .id-list {{
            list-style: none;
            margin-top: 10px;
        }}
        
        .id-item {{
            background: var(--bg-tertiary);
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
        }}
        
        .id-item:hover {{
            transform: translateX(4px);
            box-shadow: 0 2px 8px var(--shadow);
        }}
        
        .id-item code {{
            background: var(--bg-secondary);
            padding: 2px 8px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }}
        
        .remove-btn {{
            background-color: var(--accent-danger);
            color: white;
            padding: 5px 10px;
            font-size: 0.9em;
        }}
        
        .add-form {{
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }}
        
        input[type="text"] {{
            flex: 1;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 1em;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            transition: border-color 0.3s;
        }}
        
        input[type="text"]:focus {{
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
        }}
        
        .url-item {{
            background: var(--bg-tertiary);
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.2s;
        }}
        
        .url-item:hover {{
            transform: translateX(4px);
            box-shadow: 0 2px 8px var(--shadow);
        }}
        
        .url-icon {{
            font-size: 1.5em;
        }}
        
        .url-text {{
            flex: 1;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            word-break: break-all;
            color: var(--text-primary);
        }}
        
        .logs-container {{
            background: var(--bg-code);
            color: var(--text-code);
            padding: 15px;
            border-radius: 4px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            border: 1px solid var(--border-color);
        }}
        
        .log-entry {{
            margin-bottom: 8px;
            padding: 4px 0;
            animation: fadeIn 0.3s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(-5px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .log-entry.info {{
            color: var(--log-info);
        }}
        
        .log-entry.success {{
            color: var(--log-success);
        }}
        
        .log-entry.warning {{
            color: var(--log-warning);
        }}
        
        .log-entry.error {{
            color: var(--log-error);
        }}
        
        .toast-container {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .toast {{
            background: var(--bg-secondary);
            color: var(--text-primary);
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px var(--shadow);
            min-width: 300px;
            max-width: 400px;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.3s ease-out;
            border-left: 4px solid var(--accent-info);
        }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(400px); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        .toast.success {{
            border-left-color: var(--accent-primary);
        }}
        
        .toast.error {{
            border-left-color: var(--accent-danger);
        }}
        
        .toast.warning {{
            border-left-color: var(--accent-warning);
        }}
        
        .toast-icon {{
            font-size: 1.5em;
        }}
        
        .toast-message {{
            flex: 1;
        }}
        
        .toast-close {{
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 0;
            font-size: 1.2em;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 999;
            align-items: center;
            justify-content: center;
        }}
        
        .modal.show {{
            display: flex;
        }}
        
        .modal-content {{
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 12px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 8px 32px var(--shadow);
            animation: modalSlide 0.3s ease-out;
        }}
        
        @keyframes modalSlide {{
            from {{ transform: translateY(-50px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}
        
        .modal-header {{
            font-size: 1.3em;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--text-primary);
        }}
        
        .modal-body {{
            margin-bottom: 20px;
            color: var(--text-secondary);
            line-height: 1.5;
        }}
        
        .modal-footer {{
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }}
        
        .btn-secondary {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }}
    </style>
</head>
<body>
    <div class="toast-container" id="toast-container"></div>
    
    <div class="modal" id="confirmation-modal">
        <div class="modal-content">
            <div class="modal-header" id="modal-title">Confirm Action</div>
            <div class="modal-body" id="modal-message">Are you sure?</div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn-stop" id="modal-confirm" onclick="confirmAction()">Confirm</button>
            </div>
        </div>
    </div>
    
    <div class="container">
        <header>
            <div class="header-left">
                <h1>🚀 TestFlight Notifier</h1>
                <p class="version">Version {version}</p>
            </div>
            <div class="header-right">
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle Dark/Light Mode">
                    <span id="theme-icon">🌙</span>
                </button>
            </div>
        </header>
        
        <div class="card">
            <h2>📊 Performance Metrics</h2>
            <div class="metrics-grid" id="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Checks</div>
                    <div class="metric-value" id="metric-total">0</div>
                </div>
                <div class="metric-card success">
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value" id="metric-success">0%</div>
                </div>
                <div class="metric-card warning">
                    <div class="metric-label">Available</div>
                    <div class="metric-value" id="metric-available">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Checks/Min</div>
                    <div class="metric-value" id="metric-rate">0</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>⚙️ System Status</h2>
            <div class="info-grid">
                <div class="info-item">
                    <label>Status</label>
                    <div class="value">
                        <span id="status-indicator" class="status running">Running</span>
                    </div>
                </div>
                <div class="info-item">
                    <label>Check Interval</label>
                    <div class="value" id="check-interval">{check_interval}s</div>
                </div>
                <div class="info-item">
                    <label>Monitored IDs</label>
                    <div class="value" id="id-count">{len(testflight_ids)}</div>
                </div>
                <div class="info-item">
                    <label>Notification Channels</label>
                    <div class="value" id="url-count">{len(apprise_urls)}</div>
                </div>
            </div>
            
            <div class="control-buttons">
                <button class="btn-start" onclick="startMonitoring()">▶️ Start</button>
                <button class="btn-stop" onclick="showConfirmation('stop')">⏹️ Stop</button>
                <button class="btn-restart" onclick="showConfirmation('restart')">🔄 Restart</button>
                <button class="btn-refresh" onclick="refreshStatus()">↻ Refresh Status</button>
                <button class="btn-test" onclick="sendTestNotification()">🔔 Test Notification</button>
            </div>
        </div>
        
        <div class="card">
            <h2>
                📱 TestFlight IDs
                <button class="copy-btn" onclick="copyIds()">📋 Copy All</button>
            </h2>
            <div id="testflight-ids">
                <ul class="id-list" id="id-list">
                    <!-- IDs will be populated here -->
                </ul>
            </div>
            
            <div class="add-form">
                <input type="text" id="new-id" placeholder="Enter TestFlight ID (e.g., 1234567890)" />
                <button class="btn-start" onclick="addId()">➕ Add ID</button>
            </div>
        </div>
        
        <div class="card">
            <h2>
                📢 Apprise URLs
                <button class="copy-btn" onclick="copyUrls()">📋 Copy All</button>
            </h2>
            <div id="apprise-section">
                <div id="current-urls">
                    <!-- URLs will be populated here -->
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📊 Recent Activity</h2>
            <div class="logs-container" id="logs">
                <div class="log-entry info">Fetching recent logs...</div>
            </div>
        </div>
    </div>
    
    <script>
        // Global state
        let currentConfirmAction = null;
        let allIds = [];
        let allUrls = [];
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {{
            loadTheme();
            refreshStatus();
            displayIds({testflight_ids});
            displayUrls({apprise_urls});
            loadLogs();
            loadMetrics();
            
            // Auto-refresh logs and metrics
            setInterval(loadLogs, 5000);
            setInterval(loadMetrics, 10000);
            
            // Add enter key support for ID input
            document.getElementById('new-id').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    addId();
                }}
            }});
        }});
        
        // Theme Management
        function loadTheme() {{
            const theme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', theme);
            updateThemeIcon(theme);
        }}
        
        function toggleTheme() {{
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
            showToast('Theme changed to ' + newTheme + ' mode', 'success');
        }}
        
        function updateThemeIcon(theme) {{
            document.getElementById('theme-icon').textContent = theme === 'light' ? '🌙' : '☀️';
        }}
        
        // Toast Notifications
        function showToast(message, type = 'info') {{
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${{type}}`;
            
            const icons = {{
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            }};
            
            toast.innerHTML = `
                <span class="toast-icon">${{icons[type] || icons.info}}</span>
                <span class="toast-message">${{message}}</span>
                <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
            `;
            
            container.appendChild(toast);
            
            setTimeout(() => {{
                toast.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => toast.remove(), 300);
            }}, 4000);
        }}
        
        // Confirmation Modal
        function showConfirmation(action) {{
            currentConfirmAction = action;
            const modal = document.getElementById('confirmation-modal');
            const title = document.getElementById('modal-title');
            const message = document.getElementById('modal-message');
            
            if (action === 'stop') {{
                title.textContent = 'Stop Monitoring?';
                message.textContent = 'This will stop all TestFlight monitoring. You can restart it anytime.';
            }} else if (action === 'restart') {{
                title.textContent = 'Restart Monitoring?';
                message.textContent = 'This will restart the monitoring service. Any active checks will be interrupted briefly.';
            }}
            
            modal.classList.add('show');
        }}
        
        function closeModal() {{
            document.getElementById('confirmation-modal').classList.remove('show');
            currentConfirmAction = null;
        }}
        
        async function confirmAction() {{
            closeModal();
            
            if (currentConfirmAction === 'stop') {{
                await stopMonitoring();
            }} else if (currentConfirmAction === 'restart') {{
                await restartMonitoring();
            }}
        }}
        
        // Loading States
        function setButtonLoading(button, isLoading) {{
            if (isLoading) {{
                button.classList.add('loading');
                button.disabled = true;
                button.dataset.originalText = button.textContent;
                button.textContent = '';
            }} else {{
                button.classList.remove('loading');
                button.disabled = false;
                if (button.dataset.originalText) {{
                    button.textContent = button.dataset.originalText;
                }}
            }}
        }}
        
        // API Calls with Loading States
        async function refreshStatus() {{
            try {{
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const statusIndicator = document.getElementById('status-indicator');
                statusIndicator.textContent = data.monitoring ? 'Running' : 'Stopped';
                statusIndicator.className = data.monitoring ? 'status running' : 'status stopped';
                
                document.getElementById('check-interval').textContent = data.check_interval + 's';
            }} catch (error) {{
                console.error('Error fetching status:', error);
                showToast('Failed to fetch status', 'error');
            }}
        }}
        
        async function loadMetrics() {{
            try {{
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                document.getElementById('metric-total').textContent = data.total_checks || 0;
                document.getElementById('metric-success').textContent = (data.success_rate || 0).toFixed(1) + '%';
                document.getElementById('metric-available').textContent = data.available_count || 0;
                document.getElementById('metric-rate').textContent = (data.checks_per_minute || 0).toFixed(1);
            }} catch (error) {{
                console.error('Error loading metrics:', error);
            }}
        }}
        
        async function startMonitoring() {{
            const btn = event.target;
            setButtonLoading(btn, true);
            
            try {{
                const response = await fetch('/api/control/start', {{ method: 'POST' }});
                const data = await response.json();
                showToast(data.message, 'success');
                await refreshStatus();
            }} catch (error) {{
                showToast('Error starting monitoring: ' + error.message, 'error');
            }} finally {{
                setButtonLoading(btn, false);
            }}
        }}
        
        async function stopMonitoring() {{
            try {{
                const response = await fetch('/api/control/stop', {{ method: 'POST' }});
                const data = await response.json();
                showToast(data.message, 'success');
                await refreshStatus();
            }} catch (error) {{
                showToast('Error stopping monitoring: ' + error.message, 'error');
            }}
        }}
        
        async function restartMonitoring() {{
            try {{
                const response = await fetch('/api/control/restart', {{ method: 'POST' }});
                const data = await response.json();
                showToast(data.message, 'success');
                setTimeout(refreshStatus, 2000);
            }} catch (error) {{
                showToast('Error restarting monitoring: ' + error.message, 'error');
            }}
        }}
        
        async function sendTestNotification() {{
            const btn = event.target;
            setButtonLoading(btn, true);
            
            try {{
                const response = await fetch('/api/control/test-notification', {{ method: 'POST' }});
                const data = await response.json();
                
                if (response.ok) {{
                    showToast(data.message, 'success');
                }} else {{
                    showToast(data.detail || 'Test notification failed', 'error');
                }}
            }} catch (error) {{
                showToast('Error sending test notification: ' + error.message, 'error');
            }} finally {{
                setButtonLoading(btn, false);
            }}
        }}
        
        function displayIds(ids) {{
            allIds = ids;
            const container = document.getElementById('id-list');
            if (ids.length === 0) {{
                container.innerHTML = '<li style="padding: 10px;"><em>No TestFlight IDs configured</em></li>';
                return;
            }}
            
            container.innerHTML = ids.map(id => `
                <li class="id-item">
                    <code>${{id}}</code>
                    <button class="remove-btn" onclick="removeId('${{id}}')">🗑️ Remove</button>
                </li>
            `).join('');
        }}
        
        async function addId() {{
            const input = document.getElementById('new-id');
            const tfId = input.value.trim();
            
            if (!tfId) {{
                showToast('Please enter a TestFlight ID', 'warning');
                return;
            }}
            
            try {{
                const response = await fetch('/api/testflight-ids', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ testflight_id: tfId }})
                }});
                
                const data = await response.json();
                
                if (response.ok) {{
                    displayIds(data.testflight_ids);
                    document.getElementById('id-count').textContent = data.testflight_ids.length;
                    input.value = '';
                    showToast(data.message, 'success');
                }} else {{
                    showToast(`Failed to add ID: ${{data.detail || 'Unknown error'}}`, 'error');
                }}
            }} catch (error) {{
                showToast(`Error adding ID: ${{error.message}}`, 'error');
            }}
        }}
        
        async function removeId(tfId) {{
            // Show inline confirmation instead of browser alert
            const modal = document.getElementById('confirmation-modal');
            const title = document.getElementById('modal-title');
            const message = document.getElementById('modal-message');
            
            title.textContent = 'Remove TestFlight ID?';
            message.textContent = `Are you sure you want to remove ID: ${{tfId}}?`;
            
            currentConfirmAction = async () => {{
                try {{
                    const response = await fetch(`/api/testflight-ids/${{tfId}}`, {{
                        method: 'DELETE'
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        displayIds(data.testflight_ids);
                        document.getElementById('id-count').textContent = data.testflight_ids.length;
                        showToast(data.message, 'success');
                    }} else {{
                        showToast(`Failed to remove ID: ${{data.detail || 'Unknown error'}}`, 'error');
                    }}
                }} catch (error) {{
                    showToast(`Error removing ID: ${{error.message}}`, 'error');
                }}
            }};
            
            modal.classList.add('show');
            
            // Override confirm button to use our custom action
            document.getElementById('modal-confirm').onclick = () => {{
                closeModal();
                currentConfirmAction();
            }};
        }}
        
        function displayUrls(urls) {{
            allUrls = urls;
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
                
                return `
                    <div class="url-item">
                        <span class="url-icon">${{icon}}</span>
                        <span class="url-text">${{displayUrl}}</span>
                    </div>
                `;
            }}).join('');
        }}
        
        // Copy to Clipboard Functions
        async function copyIds() {{
            if (allIds.length === 0) {{
                showToast('No IDs to copy', 'warning');
                return;
            }}
            
            try {{
                await navigator.clipboard.writeText(allIds.join('\n'));
                showToast(`Copied ${{allIds.length}} TestFlight IDs to clipboard`, 'success');
            }} catch (error) {{
                showToast('Failed to copy to clipboard', 'error');
            }}
        }}
        
        async function copyUrls() {{
            if (allUrls.length === 0) {{
                showToast('No URLs to copy', 'warning');
                return;
            }}
            
            try {{
                await navigator.clipboard.writeText(allUrls.join('\n'));
                showToast(`Copied ${{allUrls.length}} Apprise URLs to clipboard`, 'success');
            }} catch (error) {{
                showToast('Failed to copy to clipboard', 'error');
            }}
        }}
        
        async function loadLogs() {{
            try {{
                const response = await fetch('/api/logs?lines=50');
                const data = await response.json();
                
                const logsContainer = document.getElementById('logs');
                if (data.logs.length === 0) {{
                    logsContainer.innerHTML = '<div class="log-entry info">No recent activity</div>';
                    return;
                }}
                
                logsContainer.innerHTML = data.logs.map(log => {{
                    let className = 'log-entry';
                    if (log.toLowerCase().includes('error')) className += ' error';
                    else if (log.toLowerCase().includes('success')) className += ' success';
                    else if (log.toLowerCase().includes('warning')) className += ' warning';
                    else className += ' info';
                    
                    return `<div class="${{className}}">${{log}}</div>`;
                }}).join('');
                
                // Auto-scroll to bottom
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }} catch (error) {{
                console.error('Error loading logs:', error);
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


@app.get("/api/metrics")
async def get_metrics():
    """Get metrics and statistics for TestFlight checks."""
    stats = _metrics.get_stats()
    return {
        "total_checks": stats["total_checks"],
        "successful_checks": stats["successful_checks"],
        "failed_checks": stats["failed_checks"],
        "status_counts": stats["status_counts"],
        "uptime_seconds": stats["uptime_seconds"],
        "checks_per_minute": round(stats["checks_per_minute"], 2),
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


@app.post("/api/testflight-ids/batch")
async def batch_operations(request: Request):
    """
    Perform batch operations on TestFlight IDs.

    Accepts JSON with:
    {
        "add": ["id1", "id2", ...],
        "remove": ["id3", "id4", ...]
    }

    Returns:
    {
        "added": {"successful": [...], "failed": [...]},
        "removed": {"successful": [...], "failed": [...]},
        "testflight_ids": [...]
    }
    """
    data = await request.json()
    ids_to_add = data.get("add", [])
    ids_to_remove = data.get("remove", [])

    result = {
        "added": {"successful": [], "failed": []},
        "removed": {"successful": [], "failed": []},
    }

    # Process additions
    for tf_id in ids_to_add:
        tf_id = tf_id.strip()
        if not tf_id:
            result["added"]["failed"].append(
                {"id": tf_id, "error": "ID cannot be empty"}
            )
            continue

        try:
            # Validate ID
            is_valid, message = await validate_testflight_id(tf_id)
            if not is_valid:
                result["added"]["failed"].append({"id": tf_id, "error": message})
                continue

            # Add to list
            success, message = add_testflight_id(tf_id)
            if success:
                result["added"]["successful"].append(tf_id)
            else:
                result["added"]["failed"].append({"id": tf_id, "error": message})
        except Exception as e:
            result["added"]["failed"].append({"id": tf_id, "error": str(e)})

    # Process removals
    for tf_id in ids_to_remove:
        tf_id = tf_id.strip()
        if not tf_id:
            result["removed"]["failed"].append(
                {"id": tf_id, "error": "ID cannot be empty"}
            )
            continue

        try:
            success, message = remove_testflight_id(tf_id)
            if success:
                result["removed"]["successful"].append(tf_id)
            else:
                result["removed"]["failed"].append({"id": tf_id, "error": message})
        except Exception as e:
            result["removed"]["failed"].append({"id": tf_id, "error": str(e)})

    result["testflight_ids"] = get_current_id_list()
    return result


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


@app.post("/api/control/test-notification")
async def test_notification():
    """Send a test notification to verify Apprise configuration."""
    try:
        msg = f"🧪 Test Notification from TestFlight Apprise Notifier\n\nTimestamp: {format_datetime(datetime.now())}\nStatus: All systems operational ✅"
        result = send_notification(msg, apobj)
        if result:
            logging.info("Test notification sent successfully")
            return {"success": True, "message": "Test notification sent successfully!"}
        else:
            logging.warning("Test notification failed to send")
            return {"success": False, "message": "Failed to send test notification. Check your Apprise URL configuration."}
    except Exception as e:
        logging.error(f"Error sending test notification: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}


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
    """Fetch and check TestFlight status using enhanced utility."""
    testflight_url = format_link(TESTFLIGHT_URL, tf_id)

    try:
        # Use the enhanced status checker utility
        result = await check_testflight_status(session, testflight_url)

        # Record metrics
        _metrics.record_check(result["status"], success=True)

        # Handle errors
        if result["status"] == TestFlightStatus.ERROR:
            logging.warning(
                "%s - %s - Error: %s",
                result.get("status_text", "Unknown"),
                tf_id,
                result.get("error", "Unknown error"),
            )
            return

        # Get app name from result or use cached function
        app_name = result.get("app_name")
        if not app_name:
            app_name = await get_app_name(TESTFLIGHT_URL, tf_id)

        # Get current and previous status
        current_status = result["status"]
        with _status_lock:
            previous_status = _previous_status.get(tf_id)
            _previous_status[tf_id] = current_status

        # Determine if we should notify
        should_notify = False
        status_changed = previous_status != current_status

        # Handle different status types
        if result["status"] == TestFlightStatus.FULL:
            logging.info(f"200 - {app_name} - Beta is full")
            # Only notify on status change to FULL (optional behavior)
            if status_changed and previous_status == TestFlightStatus.OPEN:
                should_notify = True

        elif result["status"] == TestFlightStatus.CLOSED:
            logging.info(f"200 - {app_name} - Beta is closed")
            # Don't notify for closed status

        elif result["status"] == TestFlightStatus.OPEN:
            # Beta is open - notify only if status changed or first check
            if previous_status is None or previous_status != TestFlightStatus.OPEN:
                should_notify = True
                logging.info(
                    f"200 - {app_name} - Beta is OPEN! "
                    f"(changed from {previous_status.value if previous_status else 'unknown'})"
                )
            else:
                logging.info(f"200 - {app_name} - Beta is still open (no notification)")

        else:
            # Unknown status - log for investigation
            raw_text = result.get("raw_text", "N/A")[:50]
            logging.info(f"200 - {app_name} - Unknown status: {raw_text}")

        # Send notification if status changed to something noteworthy
        if should_notify:
            notify_msg = await format_notification_link(TESTFLIGHT_URL, tf_id)
            icon_url = await get_app_icon(TESTFLIGHT_URL, tf_id)
            # Use stock TestFlight icon if app icon is unavailable
            if not icon_url or icon_url == tf_id:
                base_url = "https://developer.apple.com/assets/elements/icons"
                icon_url = f"{base_url}/testflight/testflight-64x64_2x.png"
            await send_notification_async(notify_msg, apobj, icon_url)
            logging.info(f"Notification sent for {app_name}")

    except Exception as e:
        _metrics.record_check(TestFlightStatus.ERROR, success=False)
        logging.error(f"Unexpected error fetching {tf_id}: {e}")


async def watch():
    """Check all TestFlight links."""
    try:
        current_ids = get_current_id_list()
        session = await get_http_session()
        tasks = [fetch_testflight_status(session, tf_id) for tf_id in current_ids]
        await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        logging.debug("Watch cycle cancelled during shutdown")
        raise
    except Exception as e:
        logging.error(f"Error in watch cycle: {e}")


async def heartbeat():
    """Send periodic heartbeat notifications."""
    try:
        while True:
            current_time = format_datetime(datetime.now())
            message = f"Heartbeat - {current_time}"
            send_notification(message, apobj)
            print_green(message)
            await asyncio.sleep(HEARTBEAT_INTERVAL)
    except asyncio.CancelledError:
        logging.info("Heartbeat task cancelled during shutdown")
        raise  # Re-raise to signal proper cancellation
    except Exception as e:
        logging.error(f"Error in heartbeat task: {e}")
        raise


async def start_watching():
    """Continuously check TestFlight links."""
    try:
        # Add small delay to ensure server starts first
        await asyncio.sleep(2)
        while not shutdown_event.is_set():
            await watch()
            await asyncio.sleep(SLEEP_TIME / 1000)  # Convert ms to seconds
    except asyncio.CancelledError:
        logging.info("Watching task cancelled during shutdown")
        raise  # Re-raise to signal proper cancellation
    except Exception as e:
        logging.error(f"Error in watching task: {e}")
        raise


async def start_fastapi():
    """Start FastAPI server as an async task with graceful shutdown handling."""
    server = None
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
            log_config=get_uvicorn_log_config(),  # Use custom config to preserve formatting
        )
        server = uvicorn.Server(config)
        
        # Install a custom signal handler to suppress CancelledError traceback
        async def serve_with_cancellation_handling():
            try:
                await server.serve()
            except asyncio.CancelledError:
                # Expected during shutdown/restart - don't log as error
                logging.debug("Server serve() cancelled - shutting down gracefully")
                raise
        
        await serve_with_cancellation_handling()
        
    except asyncio.CancelledError:
        logging.info("FastAPI server cancelled during shutdown/restart")
        # Initiate graceful shutdown if server was created
        if server:
            logging.debug("Initiating uvicorn server shutdown...")
            server.should_exit = True
        raise  # Re-raise to signal proper cancellation
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
