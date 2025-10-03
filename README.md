# TestFlight Apprise Notifier# TestFlight Apprise Notifier



Version 1.0.5eMonitors TestFlight beta links and sends notifications when a beta becomes available. Uses **FastAPI** for the server, **Apprise** for notifications, and **aiohttp** for asynchronous HTTP requests.



Monitors TestFlight beta links and sends notifications when slots become available. Built with FastAPI for the web server, Apprise for multi-platform notifications, and aiohttp for efficient asynchronous HTTP requests.---



---## Features



## Features### Core Functionality

- **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability

### Core Functionality- **Smart Notifications** – Sends alerts using Apprise when slots open up, including app icons as attachments for supported services (e.g., Discord, Slack)

- **TestFlight Monitoring** - Automatically checks TestFlight beta links for availability- **Enhanced Status Detection** – Improved status checking with multiple detection patterns (Open, Full, Closed, Unknown)

- **Smart Notifications** - Sends alerts using Apprise when slots open up, including app icons as attachments for supported services- **Heartbeat Notifications** – Sends periodic status updates to ensure the bot is active

- **Enhanced Status Detection** - Improved status checking with multiple detection patterns (Open, Full, Closed, Unknown)- **Graceful Shutdown** – Cleans up resources properly on exit

- **Heartbeat Notifications** - Sends periodic status updates to ensure the bot is active- **Environment Variable Validation** – Ensures required configurations are set before starting

- **Graceful Shutdown** - Cleans up resources properly on exit- **App Name Extraction** – Accurately extracts and displays app names from TestFlight pages

- **Environment Variable Validation** - Ensures required configurations are set before starting

- **App Name Extraction** - Accurately extracts and displays app names from TestFlight pages### Performance Optimizations

- **HTTP Connection Pooling** – Shared aiohttp session with connection reuse, DNS caching, and keep-alive connections for 60-80% performance improvement

### Performance Optimizations- **Circuit Breaker Pattern** – Automatic failure detection and recovery for external services with configurable thresholds

- **HTTP Connection Pooling** - Shared aiohttp session with connection reuse, DNS caching, and keep-alive connections for 60-80% performance improvement- **LRU Cache with Size Limits** – Bounded caches (100 entries each) for app names and icons to prevent memory leaks

- **Circuit Breaker Pattern** - Automatic failure detection and recovery for external services with configurable thresholds- **Optional Status Caching** – Reduce redundant requests with configurable TTL (default: 5 minutes)

- **LRU Cache with Size Limits** - Bounded caches (100 entries each) for app names and icons to prevent memory leaks- **Request Deduplication** – Efficient caching reduces unnecessary HTTP requests

- **Optional Status Caching** - Reduce redundant requests with configurable TTL (default: 5 minutes)- **Rate Limiting** – Sliding window algorithm prevents API throttling (default: 100 requests per 60 seconds)

- **Request Deduplication** - Efficient caching reduces unnecessary HTTP requests- **Exponential Backoff Retry** – Automatic retry with backoff (1s → 2s → 4s → 8s) and jitter for transient failures

- **Rate Limiting** - Sliding window algorithm prevents API throttling (default: 100 requests per 60 seconds)- **Smart Notifications** – Status change detection prevents notification spam (only notify on status changes)

- **Exponential Backoff Retry** - Automatic retry with backoff and jitter for transient failures

- **Smart Notifications** - Status change detection prevents notification spam (only notify on status changes)### Web Dashboard

- **Real-time Status** – Bot status, version, uptime, and monitoring statistics

### Web Dashboard- **Live Logs** – Recent activity with color-coded log levels and timestamps

- **Real-time Status** - Bot status, version, uptime, and monitoring statistics- **TestFlight ID Management** – Add/remove monitored apps through the web interface

- **Live Logs** - Recent activity with color-coded log levels and timestamps- **Apprise URL Management** – Add/remove notification URLs dynamically

- **TestFlight ID Management** - Add/remove monitored apps through the web interface- **Mobile-Responsive Design** – Optimized for phones, tablets, and desktops

- **Apprise URL Management** - Add/remove notification URLs dynamically with service icons- **Interactive Cards** – Collapsible sections with clean plus/minus icons

- **Mobile-Responsive Design** - Optimized for phones, tablets, and desktops- **Auto-refresh** – Dashboard updates every 30 seconds

- **Interactive Cards** - Collapsible sections with clean icons- **RESTful API** – JSON APIs for status (`/api/status`), logs (`/api/logs`), health monitoring (`/api/health`), and metrics (`/api/metrics`)

- **Auto-refresh** - Dashboard updates every 30 seconds- **Application Control** – Stop and restart the application directly from the web interface

- **RESTful API** - JSON APIs for status, logs, health monitoring, and metrics- **Batch Operations** – Efficient bulk add/remove operations via `/api/testflight-ids/batch` endpoint

- **Application Control** - Stop and restart the application directly from the web interface

- **Batch Operations** - Efficient bulk add/remove operations via API endpoint### Robustness & Monitoring

- **Health Check Endpoint** – Comprehensive system monitoring with cache stats, circuit breaker status, and HTTP session health

### Robustness & Monitoring- **Metrics & Statistics** – Track check counts, success/fail rates, and status distributions via `/api/metrics` endpoint

- **Health Check Endpoint** - Comprehensive system monitoring with cache stats, circuit breaker status, and HTTP session health- **Fault Isolation** – Circuit breakers prevent cascade failures

- **Metrics & Statistics** - Track check counts, success/fail rates, and status distributions- **Smart Timeouts** – Optimized timeouts (10s connect, 30s total) with DNS caching

- **Fault Isolation** - Circuit breakers prevent cascade failures- **Comprehensive Logging** – Python's `logging` module for better log management

- **Smart Timeouts** - Optimized timeouts with DNS caching- **Adaptive Resilience** – Graceful degradation when external services fail

- **Comprehensive Logging** - Python's logging module for better log management- **Enhanced Validation** – Format validation for TestFlight IDs (8-12 alphanumeric characters) before network checks

- **Adaptive Resilience** - Graceful degradation when external services fail

- **Enhanced Validation** - Format validation for TestFlight IDs before network checks---

- **GitHub Update Checker** - Automatic monitoring for repository updates with notifications and manual check via APIUses **FastAPI** for the server, **Apprise** for notifications, and **aiohttp** for asynchronous HTTP requests.



------



## Setup## ✨ Features



### Prerequisites✅ **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability.  

🔔 **Notifications** – Sends alerts using Apprise when slots open up, including app icons as attachments for supported services (e.g., Discord, Slack).  

- Python 3.8 or higher❤️ **Heartbeat Notifications** – Sends periodic status updates to ensure the bot is active.  

- Install dependencies:📜 **Logging** – Uses Python's `logging` module for better log management.  

🛑 **Graceful Shutdown** – Cleans up resources properly on exit.  

```bash🔧 **Environment Variable Validation** – Ensures required configurations are set before starting.  

pip install -r requirements.txt🎨 **App Name Extraction** – Accurately extracts and displays app names from TestFlight pages.  

```🌐 **Web Dashboard** – FastAPI-powered web interface with real-time status, logs, and monitoring statistics.  

🔧 **Dynamic ID Management** – Add/remove TestFlight IDs through the web dashboard without restarting the application.  

### Environment Variables📱 **Mobile-Friendly UI** – Responsive design that works perfectly on phones, tablets, and desktops.  

🎛️ **Interactive Management** – Collapsible cards for organized TestFlight ID management.  

Create a `.env` file in the project root with these values:📡 **RESTful API** – Complete API endpoints for status, logs, and TestFlight ID management.  

🛑 **Web-based Application Control** – Stop and restart the application directly from the web dashboard.  

```ini🎨 **Enhanced UI Aesthetics** – Modern gradient buttons with professional styling and responsive design.  

# List of TestFlight IDs to monitor (comma-separated)🛡️ **Security Verified** – Repository confirmed to contain no actual secrets, only test/example data.  

ID_LIST=abc123,def456,ghi789🏥 **Health Monitoring** – Comprehensive health check endpoint with system metrics and performance monitoring.  

🚀 **HTTP Optimization** – Connection pooling, DNS caching, and keep-alive for 60-80% performance improvement.  

# Apprise notification URLs (comma-separated for multiple services)⚡ **Circuit Breaker** – Automatic failure detection and recovery for external service resilience.  

APPRISE_URL=mailto://user:password@smtp.example.com,discord://webhook_id/webhook_token🧠 **Smart Caching** – LRU caches with size limits prevent memory leaks while maintaining performance.  

⚡ **Rate Limiting** – Prevents API throttling with configurable sliding window algorithm.  

# Interval in milliseconds between checks🔄 **Retry Logic** – Exponential backoff with jitter handles transient failures gracefully.  

INTERVAL_CHECK=10000📊 **Metrics Tracking** – Monitor check statistics, success rates, and status distributions.  

📦 **Batch Operations** – Efficiently manage multiple TestFlight IDs in a single request.  

# Optional: Heartbeat interval in hours (default: 6)✅ **Enhanced Validation** – Format checking ensures valid TestFlight IDs before processing.  

HEARTBEAT_INTERVAL=6🧪 **Unit Tests** – Comprehensive test coverage with pytest for reliability.  

🔄 **GitHub Update Checker** – Automatic monitoring for repository updates with notifications and manual check via API.

# Optional: FastAPI server host (default: 0.0.0.0)

FASTAPI_HOST=0.0.0.0---



# Optional: FastAPI server port (default: random 8000-9000)## ✨ Features  

FASTAPI_PORT=8080

✅ **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability.  

# Optional: GitHub update checker configuration🔔 **Notifications** – Sends alerts using Apprise when slots open up, including app icons as attachments for supported services (e.g., Discord, Slack).  

# GITHUB_REPO=klept0/TestFlight_Apprise_Notifier❤️ **Heartbeat Notifications** – Sends periodic status updates to ensure the bot is active.  

# GITHUB_BRANCH=main📜 **Logging** – Uses Python’s `logging` module for better log management.  

# GITHUB_CHECK_INTERVAL_HOURS=24  # Check every 24 hours (set to 0 to disable)🛑 **Graceful Shutdown** – Cleans up resources properly on exit.  

```🔧 **Environment Variable Validation** – Ensures required configurations are set before starting.  

🎨 **App Name Extraction** – Accurately extracts and displays app names from TestFlight pages.  

---

---

## Running the Application

## Application Control

Start the script using:

The TestFlight Apprise Notifier runs as a **single Python process** with multiple concurrent async tasks (monitoring, heartbeat, web server). The stop and restart functionality works as follows:

```bash

python main.py### Stop Functionality

```

- **Process**: Single-process application with async task coordination

The FastAPI server will be accessible via the URL shown in the console, displaying the actual IP address (e.g., `http://192.168.1.100:8080`).- **Mechanism**: Sets a shutdown event that gracefully stops all running tasks

- **Cleanup**: Properly closes HTTP connections and cleans up resources

---- **Notification**: Sends Apprise notification about the manual stop

- **Result**: Clean shutdown without data loss

## Application Control

### Restart Functionality

The TestFlight Apprise Notifier runs as a **single Python process** with multiple concurrent async tasks (monitoring, heartbeat, web server).

- **Process**: Spawns a new Python process using `subprocess.Popen`

### Stop Functionality- **Mechanism**: New instance starts immediately, then current instance shuts down

- **State**: Configuration persists via `.env` file updates

- **Process**: Single-process application with async task coordination- **Notification**: Sends Apprise notification about the restart

- **Mechanism**: Sets a shutdown event that gracefully stops all running tasks- **Zero-downtime**: New process starts before old one stops

- **Cleanup**: Properly closes HTTP connections and cleans up resources

- **Notification**: Sends Apprise notification about the manual stop### Service Operation

- **Result**: Clean shutdown without data loss

- **Not a system service**: Runs as a regular Python application

### Restart Functionality- **Manual control**: Use web dashboard buttons or send signals (Ctrl+C)

- **Process management**: Can be managed with tools like `systemd`, `supervisor`, or `pm2`

- **Process**: Spawns a new Python process using subprocess- **Resource efficient**: Single process with async I/O, minimal memory footprint

- **Mechanism**: New instance starts immediately, then current instance shuts down

- **State**: Configuration persists via .env file updates---

- **Notification**: Sends Apprise notification about the restart

- **Zero-downtime**: New process starts before old one stops## Setup



### Service Operation### Prerequisites



- **Not a system service**: Runs as a regular Python application- Python 3.8+

- **Manual control**: Use web dashboard buttons or send signals (Ctrl+C)- Install dependencies:

- **Process management**: Can be managed with tools like systemd, supervisor, or pm2

- **Resource efficient**: Single process with async I/O, minimal memory footprint```bash

pip install -r requirements.txt

---```



## Web Dashboard### Environment Variables



The web interface provides:Create a `.env` file in the project root with these values:  



- **Real-time Status** - Bot status, version, uptime, and monitoring statistics```ini

- **Live Logs** - Recent activity with color-coded log levels and timestamps# List of TestFlight IDs to monitor (comma-separated)

- **TestFlight ID Management** - Add/remove monitored apps through the web interfaceID_LIST=abc123,def456,ghi789  

- **Apprise URL Management** - Add/remove notification URLs with service logos and icons

- **Mobile-Responsive Design** - Optimized for phones, tablets, and desktops```ini

- **Interactive Cards** - Collapsible sections with clean icons# List of TestFlight IDs to monitor (comma-separated)

- **Auto-refresh** - Dashboard updates every 30 secondsID_LIST=abc123,def456,ghi789

- **API Endpoints** - JSON APIs for status, logs, health, metrics, and updates

# Apprise notification URLs (comma-separated for multiple services)

---APPRISE_URL=mailto://user:password@smtp.example.com,discord://webhook_id/webhook_token



## GitHub Update Checker# Interval in milliseconds between checks

INTERVAL_CHECK=10000

The application includes an automatic GitHub update checker that monitors the repository for new commits.

# Optional: Heartbeat interval in hours (default: 6)

### FeaturesHEARTBEAT_INTERVAL=6



- **Periodic Automatic Checks** - Runs every 24 hours by default (configurable)# Optional: FastAPI server host (default: 0.0.0.0)

- **Manual Checks via API** - Trigger update checks on-demand using curlFASTAPI_HOST=0.0.0.0

- **Smart Caching** - Avoids unnecessary API calls by caching results

- **Notifications** - Sends Apprise notifications when updates are detected# Optional: FastAPI server port (default: random 8000-9000)

- **Version Tracking** - Compares current version with latest GitHub commitFASTAPI_PORT=8080



### Manual Update Check# Optional: GitHub update checker configuration

# GITHUB_REPO=klept0/TestFlight_Apprise_Notifier

Check for updates via curl:# GITHUB_BRANCH=main

# GITHUB_CHECK_INTERVAL_HOURS=24  # Check every 24 hours (set to 0 to disable)

```bash```

# Check for updates (uses cache if available)

curl http://localhost:8080/api/updates---



# Force a fresh check (bypasses cache)## Running the Application

curl http://localhost:8080/api/updates?force=true

```Start the script using:



### Configuration```bash

python main.py

Configure update checking in your `.env` file:```



```bashThe FastAPI server will be accessible via the URL shown in the console, displaying the actual IP address (e.g., `http://192.168.1.100:8080`).

# Check every 24 hours (default), set to 0 to disable

GITHUB_CHECK_INTERVAL_HOURS=24---



# Monitor a custom repository (optional)## Web Dashboard

GITHUB_REPO=yourusername/TestFlight_Apprise_Notifier

GITHUB_BRANCH=mainThe web interface provides:

```

- **Real-time Status** – Bot status, version, uptime, and monitoring statistics

For complete documentation, see [GITHUB_UPDATE_CHECKER.md](GITHUB_UPDATE_CHECKER.md).- **Live Logs** – Recent activity with color-coded log levels and timestamps

- **TestFlight ID Management** – Add/remove monitored apps through the web interface

---- **Apprise URL Management** – Add/remove notification URLs dynamically

- **Mobile-Responsive Design** – Optimized for phones, tablets, and desktops

## Enhanced TestFlight Status Checking- **Interactive Cards** – Collapsible sections with clean plus/minus icons

- **Auto-refresh** – Dashboard updates every 30 seconds

The application includes an enhanced TestFlight status checking utility (`utils/testflight.py`) that provides:- **API Endpoints** – JSON APIs for status (`/api/status`), logs (`/api/logs`), and health (`/api/health`)



### Features---



- **Structured Status Detection** - Uses TestFlightStatus enum (OPEN, FULL, CLOSED, UNKNOWN, ERROR)## GitHub Update Checker

- **Multiple Detection Patterns** - Robust text pattern matching for accurate status detection

- **Optional Caching** - Reduce redundant requests with configurable TTL (default: 5 minutes)The application includes an automatic GitHub update checker that monitors the repository for new commits:

- **Better Error Handling** - Detailed error messages and categorization

- **Async-First Design** - Efficient concurrent checking using shared HTTP sessions### Features

- **Structured Return Values** - Complete data including app name, status, errors, and cache info

- **Periodic Automatic Checks** – Runs every 24 hours by default (configurable)

### Enabling Status Caching- **Manual Checks via API** – Trigger update checks on-demand using curl

- **Smart Caching** – Avoids unnecessary API calls by caching results

To enable status caching for improved performance:- **Notifications** – Sends Apprise notifications when updates are detected

- **Version Tracking** – Compares current version with latest GitHub commit

```python

from utils.testflight import enable_status_cache### Manual Update Check



# Enable caching with 5-minute TTLCheck for updates via curl:

enable_status_cache(ttl_seconds=300)

``````bash

# Check for updates (uses cache if available)

**Benefits of caching:**curl http://localhost:8080/api/updates

- Faster response times (1-2ms vs 200-500ms for cached entries)

- Reduced bandwidth usage# Force a fresh check (bypasses cache)

- Less load on Apple's serverscurl http://localhost:8080/api/updates?force=true

- Lower chance of hitting rate limits```



### Cache Management### Configuration



```pythonConfigure update checking in your `.env` file:

from utils.testflight import clear_status_cache, disable_status_cache

```bash

# Clear cache (keep caching enabled)# Check every 24 hours (default), set to 0 to disable

clear_status_cache()GITHUB_CHECK_INTERVAL_HOURS=24



# Disable caching completely# Monitor a custom repository (optional)

disable_status_cache()GITHUB_REPO=yourusername/TestFlight_Apprise_Notifier

```GITHUB_BRANCH=main

```

---

For complete documentation, see [GITHUB_UPDATE_CHECKER.md](GITHUB_UPDATE_CHECKER.md).

## Apprise Service Icons

---

The web dashboard displays official service logos for configured Apprise notification URLs, making it easy to identify and manage your notification services at a glance.

## Enhanced TestFlight Status Checking

**Supported services include:**

- Discord, Slack, Telegram, Matrix, Mattermost, SignalThe application now includes an enhanced TestFlight status checking utility (`utils/testflight.py`) that provides:

- Pushover, Pushbullet, Gotify, ntfy

- Email (Gmail)### Features

- PagerDuty, Opsgenie

- Microsoft Teams, Webex- **Structured Status Detection** – Uses `TestFlightStatus` enum (OPEN, FULL, CLOSED, UNKNOWN, ERROR)

- Home Assistant- **Multiple Detection Patterns** – Robust text pattern matching for accurate status detection

- Webhooks, JSON, XML- **Optional Caching** – Reduce redundant requests with configurable TTL (default: 5 minutes)

- And 30+ more services- **Better Error Handling** – Detailed error messages and categorization

- **Async-First Design** – Efficient concurrent checking using shared HTTP sessions

For complete documentation, see [APPRISE_ICON_DISPLAY.md](APPRISE_ICON_DISPLAY.md).- **Structured Return Values** – Complete data including app name, status, errors, and cache info



---### Enabling Status Caching (Optional)



## API EndpointsTo enable status caching for improved performance, add this to your startup code:



### Health & Status```python

- `GET /api/health` - System health check with metricsfrom utils.testflight import enable_status_cache

- `GET /api/metrics` - Check statistics and success rates

- `GET /api/logs` - Recent activity logs# Enable caching with 5-minute TTL

enable_status_cache(ttl_seconds=300)

### TestFlight Management```

- `GET /api/testflight-ids` - List configured TestFlight IDs

- `GET /api/testflight-ids/details` - Detailed information for each ID**Benefits of caching:**

- `POST /api/testflight-ids/add` - Add a new TestFlight ID- Faster response times (1-2ms vs 200-500ms for cached entries)

- `POST /api/testflight-ids/remove` - Remove a TestFlight ID- Reduced bandwidth usage

- `POST /api/testflight-ids/batch` - Batch add/remove operations- Less load on Apple's servers

- Lower chance of hitting rate limits

### Apprise Management

- `GET /api/apprise-urls` - List configured Apprise URLs with service info### Cache Management

- `POST /api/apprise-urls/validate` - Validate an Apprise URL

- `POST /api/apprise-urls/add` - Add a new Apprise URL```python

- `POST /api/apprise-urls/remove` - Remove an Apprise URLfrom utils.testflight import clear_status_cache, disable_status_cache



### Application Control# Clear cache (keep caching enabled)

- `POST /api/control/stop` - Stop the applicationclear_status_cache()

- `POST /api/control/restart` - Restart the application

# Disable caching completely

### Updatesdisable_status_cache()

- `GET /api/updates` - Check for GitHub repository updates```

- `GET /api/updates?force=true` - Force a fresh update check

---

---

## Utility Functions

## Utility Functions

- **`utils/notifications.py`** – Handles notifications with error handling and icon attachments

- **utils/notifications.py** - Handles notifications with error handling and icon attachments- **`utils/formatting.py`** – Provides functions for formatting dates, links, and extracting app names/icons

- **utils/formatting.py** - Provides functions for formatting dates, links, and extracting app names/icons- **`utils/colors.py`** – Adds color-coded console output for better visibility

- **utils/colors.py** - Adds color-coded console output for better visibility- **`utils/testflight.py`** – Enhanced TestFlight status checking with caching and structured detection

- **utils/testflight.py** - Enhanced TestFlight status checking with caching and structured detection

---

---

## Logging

## Logging

The application logs messages in the console with timestamps and log levels:

The application logs messages in the console with timestamps and log levels:

```plaintext

```plaintext2025-09-24 19:00:00 - INFO - Starting TestFlight Apprise Notifier v1.0.5c [v1.0.5c]

2025-10-03 12:00:00 - INFO - Starting TestFlight Apprise Notifier v1.0.5e2025-09-24 19:00:05 - INFO - Starting FastAPI server on 0.0.0.0:8080

2025-10-03 12:00:05 - INFO - Starting FastAPI server on 0.0.0.0:80802025-09-24 19:01:00 - INFO - 200 - My Awesome App - Beta is OPEN! Notification sent

2025-10-03 12:01:00 - INFO - 200 - My Awesome App - Beta is OPEN! Notification sent2025-09-24 19:01:05 - INFO - Notification sent: Slots available for My Awesome App

2025-10-03 12:01:05 - INFO - Notification sent: Slots available for My Awesome App```

```

---

---

## Heartbeat Notifications

## Heartbeat Notifications

To confirm the bot is running, it sends a **heartbeat notification** periodically (default: every 6 hours).

To confirm the bot is running, it sends a **heartbeat notification** periodically (default: every 6 hours).

You can customize the heartbeat interval by setting the `HEARTBEAT_INTERVAL` environment variable (in hours):

You can customize the heartbeat interval by setting the `HEARTBEAT_INTERVAL` environment variable (in hours):

```ini

```iniHEARTBEAT_INTERVAL=12  # Send heartbeat every 12 hours

HEARTBEAT_INTERVAL=12  # Send heartbeat every 12 hours```

```

Example Heartbeat Message:

Example Heartbeat Message:

```plaintext

```plaintextHeartbeat - 2025-09-24 19:00:00

Heartbeat - 2025-10-03 12:00:00```

```

---

---

## Graceful Shutdown

## Docker Support

The bot handles **SIGINT** and **SIGTERM** signals to properly close connections before stopping.

The application can be run in a Docker container for easy deployment and isolation.

---

For complete Docker documentation, see [DOCKER.md](DOCKER.md).

## Contributing

Quick start:

Want to help improve this project? Feel free to **submit issues** or **create a pull request**!

```bash

# Build the image---

docker build -t testflight-notifier .

## License

# Run the container

docker run -d --name testflight-notifier \This project is licensed under the **MIT License**.

  --env-file .env \

  -p 8080:8080 \---

  testflight-notifier

```## Releases



Or use Docker Compose:To create a new release, follow these steps:



```bash1. Update the version number in `main.py`.

docker-compose up -d2. Update the `CHANGELOG.md` file with the changes for the new release.

```3. Commit the changes and push to the `main` branch.

4. Create a new tag for the release:

---

```bash

## Testinggit tag -a vX.X.X -m "Release vX.X.X"

git push origin vX.X.X

The project includes comprehensive unit tests using pytest:```



```bash5. The GitHub Actions workflow will automatically create a new release and upload the assets.

# Install test dependencies

pip install -r tests/requirements-test.txtFor more details, see the [CHANGELOG.md](./CHANGELOG.md) file.


# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

---

## Graceful Shutdown

The bot handles **SIGINT** and **SIGTERM** signals to properly close connections before stopping.

---

## Contributing

Want to help improve this project? Feel free to submit issues or create a pull request!

---

## License

This project is licensed under the **MIT License**.

---

## Releases

To create a new release:

1. Update the version number in `main.py`
2. Update the `CHANGELOG.md` file with the changes
3. Commit the changes and push to the main branch
4. Create a new tag for the release:

```bash
git tag -a v1.0.5e -m "Release v1.0.5e"
git push origin v1.0.5e
```

The GitHub Actions workflow will automatically create a new release and upload the assets.

For version history, see [CHANGELOG.md](CHANGELOG.md).
