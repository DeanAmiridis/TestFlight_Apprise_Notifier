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
from fastapi import FastAPI
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime
from utils.notifications import send_notification, send_notification_async
from utils.formatting import (
    format_datetime,
    format_link,
    format_notification_link,
    get_app_icon,
)
from utils.colors import print_green

# Version
__version__ = "1.0.3"

# Load environment variables
load_dotenv()

# Constants
TESTFLIGHT_URL = "https://testflight.apple.com/join/"
FULL_TEXT = "This beta is full."
NOT_OPEN_TEXT = "This beta isn't accepting any new testers right now."
id_list_raw = os.getenv("ID_LIST", "").split(",")
SLEEP_TIME = int(os.getenv("INTERVAL_CHECK", "10000"))  # in ms
TITLE_REGEX = re.compile(r"Join the (.+) beta - TestFlight - Apple")
apprise_urls_raw = os.getenv("APPRISE_URL", "").split(",")
HEARTBEAT_INTERVAL = 6 * 60 * 60  # 6 hours in seconds

# Configure logging
format_str = f"%(asctime)s - %(levelname)s - %(message)s [v{__version__}]"
logging.basicConfig(level=logging.INFO, format=format_str)

# Validate environment variables
ID_LIST = [tf_id.strip() for tf_id in id_list_raw if tf_id.strip()]
APPRISE_URLS = [url.strip() for url in apprise_urls_raw if url.strip()]

# Constants
TESTFLIGHT_URL = "https://testflight.apple.com/join/"
FULL_TEXT = "This beta is full."
NOT_OPEN_TEXT = "This beta isn't accepting any new testers right now."
ID_LIST = os.getenv("ID_LIST", "").split(",")
SLEEP_TIME = int(os.getenv("INTERVAL_CHECK", 10000))  # in ms
TITLE_REGEX = re.compile(r"Join the (.+) beta - TestFlight - Apple")
APPRISE_URLS = os.getenv("APPRISE_URL", "").split(",")
HEARTBEAT_INTERVAL = 6 * 60 * 60  # 6 hours in seconds

# Configure logging
format_str = f"%(asctime)s - %(levelname)s - %(message)s [v{__version__}]"
logging.basicConfig(level=logging.INFO, format=format_str)

# Validate environment variables
ID_LIST = [tf_id.strip() for tf_id in ID_LIST if tf_id.strip()]
APPRISE_URLS = [url.strip() for url in APPRISE_URLS if url.strip()]

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

# Graceful shutdown (cross-platform compatibility)
shutdown_event = asyncio.Event()


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


@app.get("/")
async def home():
    return {"status": "Bot is alive"}


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

            if status_text in [NOT_OPEN_TEXT, FULL_TEXT]:
                logging.info(f"{response.status} - {tf_id} - {status_text}")
                return

            title_tag = soup.find("title")
            title = title_tag.text if title_tag else "Unknown"
            title_match = TITLE_REGEX.search(title)
            notify_msg = await format_notification_link(TESTFLIGHT_URL, tf_id)
            icon_url = await get_app_icon(TESTFLIGHT_URL, tf_id)
            await send_notification_async(notify_msg, apobj, icon_url)
            logging.info(
                f"{response.status} - {tf_id} - {title_match.group(1) if title_match else 'Unknown'} - {status_text}"
            )
    except aiohttp.ClientResponseError as e:
        logging.error(f"HTTP error fetching {tf_id} (URL: {testflight_url}): {e}")
    except aiohttp.ClientError as e:
        logging.error(f"Network error fetching {tf_id} (URL: {testflight_url}): {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching {tf_id} (URL: {testflight_url}): {e}")


async def watch():
    """Check all TestFlight links."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_testflight_status(session, tf_id) for tf_id in ID_LIST]
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
    while not shutdown_event.is_set():
        await watch()
        await asyncio.sleep(SLEEP_TIME / 1000)  # Convert ms to seconds


def start_fastapi():
    """Start FastAPI server with default host and port."""
    default_host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    default_port = int(os.getenv("FASTAPI_PORT", random.randint(8000, 9000)))

    logging.info(f"Starting FastAPI server on {default_host}:{default_port}")
    uvicorn.run(app, host=default_host, port=default_port)


def main():
    """Main function to start all tasks."""
    threading.Thread(target=start_fastapi, daemon=True).start()
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
    try:
        await asyncio.gather(start_watching(), heartbeat(), shutdown_event.wait())
    except asyncio.CancelledError:
        logging.info("Async tasks cancelled during shutdown.")
    finally:
        logging.info("Async main loop has exited.")


if __name__ == "__main__":
    main()
