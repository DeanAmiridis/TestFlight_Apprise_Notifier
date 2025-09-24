import logging
import asyncio


def send_notification(message: str, apobj):
    """Send notification using Apprise with error handling."""
    try:
        apobj.notify(body=message, title="TestFlight Alert")
        logging.info(f"Notification sent: {message}")
    except Exception as e:
        logging.error(f"Error sending notification: {e}")


async def send_notification_async(message: str, apobj):
    """Send notification asynchronously."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_notification, message, apobj)
