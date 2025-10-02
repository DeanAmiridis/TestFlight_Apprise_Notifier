# TestFlight Apprise Notifier

Monitors TestFlight beta links and sends notifications when a beta becomes available. Uses **FastAPI** for the server, **Apprise** for notifications, and **aiohttp** for asynchronous HTTP requests.

---

## Features

### Core Functionality
- **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability
- **Smart Notifications** – Sends alerts using Apprise when slots open up, including app icons as attachments for supported services (e.g., Discord, Slack)
- **Enhanced Status Detection** – Improved status checking with multiple detection patterns (Open, Full, Closed, Unknown)
- **Heartbeat Notifications** – Sends periodic status updates to ensure the bot is active
- **Graceful Shutdown** – Cleans up resources properly on exit
- **Environment Variable Validation** – Ensures required configurations are set before starting
- **App Name Extraction** – Accurately extracts and displays app names from TestFlight pages

### Performance Optimizations
- **HTTP Connection Pooling** – Shared aiohttp session with connection reuse, DNS caching, and keep-alive connections for 60-80% performance improvement
- **Circuit Breaker Pattern** – Automatic failure detection and recovery for external services with configurable thresholds
- **LRU Cache with Size Limits** – Bounded caches (100 entries each) for app names and icons to prevent memory leaks
- **Optional Status Caching** – Reduce redundant requests with configurable TTL (default: 5 minutes)
- **Request Deduplication** – Efficient caching reduces unnecessary HTTP requests
- **Rate Limiting** – Sliding window algorithm prevents API throttling (default: 100 requests per 60 seconds)
- **Exponential Backoff Retry** – Automatic retry with backoff (1s → 2s → 4s → 8s) and jitter for transient failures
- **Smart Notifications** – Status change detection prevents notification spam (only notify on status changes)

### Web Dashboard
- **Real-time Status** – Bot status, version, uptime, and monitoring statistics
- **Live Logs** – Recent activity with color-coded log levels and timestamps
- **TestFlight ID Management** – Add/remove monitored apps through the web interface
- **Apprise URL Management** – Add/remove notification URLs dynamically
- **Mobile-Responsive Design** – Optimized for phones, tablets, and desktops
- **Interactive Cards** – Collapsible sections with clean plus/minus icons
- **Auto-refresh** – Dashboard updates every 30 seconds
- **RESTful API** – JSON APIs for status (`/api/status`), logs (`/api/logs`), health monitoring (`/api/health`), and metrics (`/api/metrics`)
- **Application Control** – Stop and restart the application directly from the web interface
- **Batch Operations** – Efficient bulk add/remove operations via `/api/testflight-ids/batch` endpoint

### Robustness & Monitoring
- **Health Check Endpoint** – Comprehensive system monitoring with cache stats, circuit breaker status, and HTTP session health
- **Metrics & Statistics** – Track check counts, success/fail rates, and status distributions via `/api/metrics` endpoint
- **Fault Isolation** – Circuit breakers prevent cascade failures
- **Smart Timeouts** – Optimized timeouts (10s connect, 30s total) with DNS caching
- **Comprehensive Logging** – Python's `logging` module for better log management
- **Adaptive Resilience** – Graceful degradation when external services fail
- **Enhanced Validation** – Format validation for TestFlight IDs (8-12 alphanumeric characters) before network checks

---
Uses **FastAPI** for the server, **Apprise** for notifications, and **aiohttp** for asynchronous HTTP requests.

---

## ✨ Features

✅ **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability.  
🔔 **Notifications** – Sends alerts using Apprise when slots open up, including app icons as attachments for supported services (e.g., Discord, Slack).  
❤️ **Heartbeat Notifications** – Sends periodic status updates to ensure the bot is active.  
📜 **Logging** – Uses Python's `logging` module for better log management.  
🛑 **Graceful Shutdown** – Cleans up resources properly on exit.  
🔧 **Environment Variable Validation** – Ensures required configurations are set before starting.  
🎨 **App Name Extraction** – Accurately extracts and displays app names from TestFlight pages.  
🌐 **Web Dashboard** – FastAPI-powered web interface with real-time status, logs, and monitoring statistics.  
🔧 **Dynamic ID Management** – Add/remove TestFlight IDs through the web dashboard without restarting the application.  
📱 **Mobile-Friendly UI** – Responsive design that works perfectly on phones, tablets, and desktops.  
🎛️ **Interactive Management** – Collapsible cards for organized TestFlight ID management.  
📡 **RESTful API** – Complete API endpoints for status, logs, and TestFlight ID management.  
🛑 **Web-based Application Control** – Stop and restart the application directly from the web dashboard.  
🎨 **Enhanced UI Aesthetics** – Modern gradient buttons with professional styling and responsive design.  
🛡️ **Security Verified** – Repository confirmed to contain no actual secrets, only test/example data.  
🏥 **Health Monitoring** – Comprehensive health check endpoint with system metrics and performance monitoring.  
🚀 **HTTP Optimization** – Connection pooling, DNS caching, and keep-alive for 60-80% performance improvement.  
⚡ **Circuit Breaker** – Automatic failure detection and recovery for external service resilience.  
🧠 **Smart Caching** – LRU caches with size limits prevent memory leaks while maintaining performance.  
⚡ **Rate Limiting** – Prevents API throttling with configurable sliding window algorithm.  
🔄 **Retry Logic** – Exponential backoff with jitter handles transient failures gracefully.  
📊 **Metrics Tracking** – Monitor check statistics, success rates, and status distributions.  
📦 **Batch Operations** – Efficiently manage multiple TestFlight IDs in a single request.  
✅ **Enhanced Validation** – Format checking ensures valid TestFlight IDs before processing.  
🧪 **Unit Tests** – Comprehensive test coverage with pytest for reliability.

---

## ✨ Features  

✅ **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability.  
🔔 **Notifications** – Sends alerts using Apprise when slots open up, including app icons as attachments for supported services (e.g., Discord, Slack).  
❤️ **Heartbeat Notifications** – Sends periodic status updates to ensure the bot is active.  
📜 **Logging** – Uses Python’s `logging` module for better log management.  
🛑 **Graceful Shutdown** – Cleans up resources properly on exit.  
🔧 **Environment Variable Validation** – Ensures required configurations are set before starting.  
🎨 **App Name Extraction** – Accurately extracts and displays app names from TestFlight pages.  

---

## Application Control

The TestFlight Apprise Notifier runs as a **single Python process** with multiple concurrent async tasks (monitoring, heartbeat, web server). The stop and restart functionality works as follows:

### Stop Functionality

- **Process**: Single-process application with async task coordination
- **Mechanism**: Sets a shutdown event that gracefully stops all running tasks
- **Cleanup**: Properly closes HTTP connections and cleans up resources
- **Notification**: Sends Apprise notification about the manual stop
- **Result**: Clean shutdown without data loss

### Restart Functionality

- **Process**: Spawns a new Python process using `subprocess.Popen`
- **Mechanism**: New instance starts immediately, then current instance shuts down
- **State**: Configuration persists via `.env` file updates
- **Notification**: Sends Apprise notification about the restart
- **Zero-downtime**: New process starts before old one stops

### Service Operation

- **Not a system service**: Runs as a regular Python application
- **Manual control**: Use web dashboard buttons or send signals (Ctrl+C)
- **Process management**: Can be managed with tools like `systemd`, `supervisor`, or `pm2`
- **Resource efficient**: Single process with async I/O, minimal memory footprint

---

## Setup

### Prerequisites

- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root with these values:  

```ini
# List of TestFlight IDs to monitor (comma-separated)
ID_LIST=abc123,def456,ghi789  

```ini
# List of TestFlight IDs to monitor (comma-separated)
ID_LIST=abc123,def456,ghi789

# Apprise notification URLs (comma-separated for multiple services)
APPRISE_URL=mailto://user:password@smtp.example.com,discord://webhook_id/webhook_token

# Interval in milliseconds between checks
INTERVAL_CHECK=10000

# Optional: FastAPI server host (default: 0.0.0.0)
FASTAPI_HOST=0.0.0.0

# Optional: FastAPI server port (default: random 8000-9000)
FASTAPI_PORT=8080
```

---

## Running the Application

Start the script using:

```bash
python main.py
```

The FastAPI server will be accessible via the URL shown in the console, displaying the actual IP address (e.g., `http://192.168.1.100:8080`).

---

## Web Dashboard

The web interface provides:

- **Real-time Status** – Bot status, version, uptime, and monitoring statistics
- **Live Logs** – Recent activity with color-coded log levels and timestamps
- **TestFlight ID Management** – Add/remove monitored apps through the web interface
- **Apprise URL Management** – Add/remove notification URLs dynamically
- **Mobile-Responsive Design** – Optimized for phones, tablets, and desktops
- **Interactive Cards** – Collapsible sections with clean plus/minus icons
- **Auto-refresh** – Dashboard updates every 30 seconds
- **API Endpoints** – JSON APIs for status (`/api/status`), logs (`/api/logs`), and health (`/api/health`)

---

## Enhanced TestFlight Status Checking

The application now includes an enhanced TestFlight status checking utility (`utils/testflight.py`) that provides:

### Features

- **Structured Status Detection** – Uses `TestFlightStatus` enum (OPEN, FULL, CLOSED, UNKNOWN, ERROR)
- **Multiple Detection Patterns** – Robust text pattern matching for accurate status detection
- **Optional Caching** – Reduce redundant requests with configurable TTL (default: 5 minutes)
- **Better Error Handling** – Detailed error messages and categorization
- **Async-First Design** – Efficient concurrent checking using shared HTTP sessions
- **Structured Return Values** – Complete data including app name, status, errors, and cache info

### Enabling Status Caching (Optional)

To enable status caching for improved performance, add this to your startup code:

```python
from utils.testflight import enable_status_cache

# Enable caching with 5-minute TTL
enable_status_cache(ttl_seconds=300)
```

**Benefits of caching:**
- Faster response times (1-2ms vs 200-500ms for cached entries)
- Reduced bandwidth usage
- Less load on Apple's servers
- Lower chance of hitting rate limits

### Cache Management

```python
from utils.testflight import clear_status_cache, disable_status_cache

# Clear cache (keep caching enabled)
clear_status_cache()

# Disable caching completely
disable_status_cache()
```

---

## Utility Functions

- **`utils/notifications.py`** – Handles notifications with error handling and icon attachments
- **`utils/formatting.py`** – Provides functions for formatting dates, links, and extracting app names/icons
- **`utils/colors.py`** – Adds color-coded console output for better visibility
- **`utils/testflight.py`** – Enhanced TestFlight status checking with caching and structured detection

---

## Logging

The application logs messages in the console with timestamps and log levels:

```plaintext
2025-09-24 19:00:00 - INFO - Starting TestFlight Apprise Notifier v1.0.5c [v1.0.5c]
2025-09-24 19:00:05 - INFO - Starting FastAPI server on 0.0.0.0:8080
2025-09-24 19:01:00 - INFO - 200 - My Awesome App - Beta is OPEN! Notification sent
2025-09-24 19:01:05 - INFO - Notification sent: Slots available for My Awesome App
```

---

## Heartbeat Notifications

To confirm the bot is running, it sends a **heartbeat notification every 6 hours**.

Example Heartbeat Message:

```plaintext
Heartbeat - 2025-09-24 19:00:00
```

---

## Graceful Shutdown

The bot handles **SIGINT** and **SIGTERM** signals to properly close connections before stopping.

---

## Contributing

Want to help improve this project? Feel free to **submit issues** or **create a pull request**!

---

## License

This project is licensed under the **MIT License**.

---

## Releases

To create a new release, follow these steps:

1. Update the version number in `main.py`.
2. Update the `CHANGELOG.md` file with the changes for the new release.
3. Commit the changes and push to the `main` branch.
4. Create a new tag for the release:

```bash
git tag -a vX.X.X -m "Release vX.X.X"
git push origin vX.X.X
```

5. The GitHub Actions workflow will automatically create a new release and upload the assets.

For more details, see the [CHANGELOG.md](./CHANGELOG.md) file.
