import logging
import asyncio


def send_notification(message: str, apobj, icon_url: str = ""):
    """Send notification using Apprise with error handling.

    Apprise does not provide a generic `attach()` method on the core object.
    To include an icon, most notification services rely on their own plugin
    parameters or simply render links in the body. For broad compatibility,
    we append the icon URL (if provided) to the message body.
    """
    try:
        body = message
        if icon_url:
            # Append icon URL on new line for visibility without breaking services
            body = f"{message}\nIcon: {icon_url}"
        apobj.notify(body=body, title="TestFlight Alert")
        logging.info(f"Notification sent: {message}")
    except Exception as e:
        logging.error(f"Error sending notification: {e}")


async def send_notification_async(message: str, apobj, icon_url: str = ""):
    """Send notification asynchronously."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_notification, message, apobj, icon_url)
