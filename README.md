# TestFlight Apprise Notifier# TestFlight Apprise Notifier# TestFlight Apprise Notifier



**Version 1.0.5e**



Monitors TestFlight beta links and sends notifications when slots become available. Built with FastAPI for the web server, Apprise for multi-platform notifications, and aiohttp for efficient asynchronous HTTP requests.Version 1.0.5eMonitors TestFlight beta links and sends notifications when a beta becomes available. Uses **FastAPI** for the server, **Apprise** for notifications, and **aiohttp** for asynchronous HTTP requests.



---



## FeaturesMonitors TestFlight beta links and sends notifications when slots become available. Built with FastAPI for the web server, Apprise for multi-platform notifications, and aiohttp for efficient asynchronous HTTP requests.---



### Core Functionality



- **TestFlight Monitoring** - Automatically checks TestFlight beta links for availability---## Features

- **Smart Notifications** - Sends alerts using Apprise when slots open up, including app icons as attachments for supported services (e.g., Discord, Slack)

- **Enhanced Status Detection** - Improved status checking with multiple detection patterns (Open, Full, Closed, Unknown)

- **Heartbeat Notifications** - Sends periodic status updates to ensure the bot is active

- **Graceful Shutdown** - Cleans up resources properly on exit## Features### Core Functionality

- **Environment Variable Validation** - Ensures required configurations are set before starting

- **App Name Extraction** - Accurately extracts and displays app names from TestFlight pages- **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability

- **GitHub Update Checker** - Automatic monitoring for repository updates with notifications and manual check via API

### Core Functionality- **Smart Notifications** – Sends alerts using Apprise when slots open up, including app icons as attachments for supported services (e.g., Discord, Slack)

### Performance Optimizations

- **TestFlight Monitoring** - Automatically checks TestFlight beta links for availability- **Enhanced Status Detection** – Improved status checking with multiple detection patterns (Open, Full, Closed, Unknown)

- **HTTP Connection Pooling** - Shared aiohttp session with connection reuse, DNS caching, and keep-alive connections for 60-80% performance improvement

- **Circuit Breaker Pattern** - Automatic failure detection and recovery for external services with configurable thresholds- **Smart Notifications** - Sends alerts using Apprise when slots open up, including app icons as attachments for supported services- **Heartbeat Notifications** – Sends periodic status updates to ensure the bot is active

- **LRU Cache with Size Limits** - Bounded caches (100 entries each) for app names and icons to prevent memory leaks

- **Optional Status Caching** - Reduce redundant requests with configurable TTL (default: 5 minutes)- **Enhanced Status Detection** - Improved status checking with multiple detection patterns (Open, Full, Closed, Unknown)- **Graceful Shutdown** – Cleans up resources properly on exit

- **Request Deduplication** - Efficient caching reduces unnecessary HTTP requests

- **Rate Limiting** - Sliding window algorithm prevents API throttling (default: 100 requests per 60 seconds)- **Heartbeat Notifications** - Sends periodic status updates to ensure the bot is active- **Environment Variable Validation** – Ensures required configurations are set before starting

- **Exponential Backoff Retry** - Automatic retry with backoff (1s, 2s, 4s, 8s) and jitter for transient failures

- **Smart Notifications** - Status change detection prevents notification spam (only notify on status changes)- **Graceful Shutdown** - Cleans up resources properly on exit- **App Name Extraction** – Accurately extracts and displays app names from TestFlight pages



### Web Dashboard- **Environment Variable Validation** - Ensures required configurations are set before starting



- **Real-time Status** - Bot status, version, uptime, and monitoring statistics- **App Name Extraction** - Accurately extracts and displays app names from TestFlight pages### Performance Optimizations

- **Live Logs** - Recent activity with color-coded log levels and timestamps

- **TestFlight ID Management** - Add/remove monitored apps through the web interface- **HTTP Connection Pooling** – Shared aiohttp session with connection reuse, DNS caching, and keep-alive connections for 60-80% performance improvement

- **Apprise URL Management** - Add/remove notification URLs dynamically with service icons

- **Mobile-Responsive Design** - Optimized for phones, tablets, and desktops### Performance Optimizations- **Circuit Breaker Pattern** – Automatic failure detection and recovery for external services with configurable thresholds

- **Interactive Cards** - Collapsible sections with clean icons

- **Auto-refresh** - Dashboard updates every 30 seconds- **HTTP Connection Pooling** - Shared aiohttp session with connection reuse, DNS caching, and keep-alive connections for 60-80% performance improvement- **LRU Cache with Size Limits** – Bounded caches (100 entries each) for app names and icons to prevent memory leaks

- **RESTful API** - JSON APIs for status (`/api/status`), logs (`/api/logs`), health monitoring (`/api/health`), and metrics (`/api/metrics`)

- **Application Control** - Stop and restart the application directly from the web interface- **Circuit Breaker Pattern** - Automatic failure detection and recovery for external services with configurable thresholds- **Optional Status Caching** – Reduce redundant requests with configurable TTL (default: 5 minutes)

- **Batch Operations** - Efficient bulk add/remove operations via `/api/testflight-ids/batch` endpoint

- **LRU Cache with Size Limits** - Bounded caches (100 entries each) for app names and icons to prevent memory leaks- **Request Deduplication** – Efficient caching reduces unnecessary HTTP requests

### Robustness & Monitoring

- **Optional Status Caching** - Reduce redundant requests with configurable TTL (default: 5 minutes)- **Rate Limiting** – Sliding window algorithm prevents API throttling (default: 100 requests per 60 seconds)

- **Health Check Endpoint** - Comprehensive system monitoring with cache stats, circuit breaker status, and HTTP session health

- **Metrics & Statistics** - Track check counts, success/fail rates, and status distributions via `/api/metrics` endpoint- **Request Deduplication** - Efficient caching reduces unnecessary HTTP requests- **Exponential Backoff Retry** – Automatic retry with backoff (1s → 2s → 4s → 8s) and jitter for transient failures

- **Fault Isolation** - Circuit breakers prevent cascade failures

- **Smart Timeouts** - Optimized timeouts (10s connect, 30s total) with DNS caching- **Rate Limiting** - Sliding window algorithm prevents API throttling (default: 100 requests per 60 seconds)- **Smart Notifications** – Status change detection prevents notification spam (only notify on status changes)

- **Comprehensive Logging** - Python's `logging` module for better log management

- **Adaptive Resilience** - Graceful degradation when external services fail- **Exponential Backoff Retry** - Automatic retry with backoff and jitter for transient failures

- **Enhanced Validation** - Format validation for TestFlight IDs (8-12 alphanumeric characters) before network checks

- **Smart Notifications** - Status change detection prevents notification spam (only notify on status changes)### Web Dashboard

---

- **Real-time Status** – Bot status, version, uptime, and monitoring statistics

## Setup

### Web Dashboard- **Live Logs** – Recent activity with color-coded log levels and timestamps

### Prerequisites

- **Real-time Status** - Bot status, version, uptime, and monitoring statistics- **TestFlight ID Management** – Add/remove monitored apps through the web interface

- Python 3.8 or higher

- Install dependencies:- **Live Logs** - Recent activity with color-coded log levels and timestamps- **Apprise URL Management** – Add/remove notification URLs dynamically



```bash- **TestFlight ID Management** - Add/remove monitored apps through the web interface- **Mobile-Responsive Design** – Optimized for phones, tablets, and desktops

pip install -r requirements.txt

```- **Apprise URL Management** - Add/remove notification URLs dynamically with service icons- **Interactive Cards** – Collapsible sections with clean plus/minus icons



### Environment Variables- **Mobile-Responsive Design** - Optimized for phones, tablets, and desktops- **Auto-refresh** – Dashboard updates every 30 seconds



Create a `.env` file in the project root with these values:- **Interactive Cards** - Collapsible sections with clean icons- **RESTful API** – JSON APIs for status (`/api/status`), logs (`/api/logs`), health monitoring (`/api/health`), and metrics (`/api/metrics`)



```ini- **Auto-refresh** - Dashboard updates every 30 seconds- **Application Control** – Stop and restart the application directly from the web interface

# List of TestFlight IDs to monitor (comma-separated)

ID_LIST=abc123,def456,ghi789- **RESTful API** - JSON APIs for status, logs, health monitoring, and metrics- **Batch Operations** – Efficient bulk add/remove operations via `/api/testflight-ids/batch` endpoint



# Apprise notification URLs (comma-separated for multiple services)- **Application Control** - Stop and restart the application directly from the web interface

APPRISE_URL=mailto://user:password@smtp.example.com,discord://webhook_id/webhook_token

- **Batch Operations** - Efficient bulk add/remove operations via API endpoint### Robustness & Monitoring

# Interval in milliseconds between checks

INTERVAL_CHECK=10000- **Health Check Endpoint** – Comprehensive system monitoring with cache stats, circuit breaker status, and HTTP session health



# Optional: Heartbeat interval in hours (default: 6)### Robustness & Monitoring- **Metrics & Statistics** – Track check counts, success/fail rates, and status distributions via `/api/metrics` endpoint

HEARTBEAT_INTERVAL=6

- **Health Check Endpoint** - Comprehensive system monitoring with cache stats, circuit breaker status, and HTTP session health- **Fault Isolation** – Circuit breakers prevent cascade failures

# Optional: FastAPI server host (default: 0.0.0.0)

FASTAPI_HOST=0.0.0.0- **Metrics & Statistics** - Track check counts, success/fail rates, and status distributions- **Smart Timeouts** – Optimized timeouts (10s connect, 30s total) with DNS caching



# Optional: FastAPI server port (default: random 8000-9000)- **Fault Isolation** - Circuit breakers prevent cascade failures- **Comprehensive Logging** – Python's `logging` module for better log management

FASTAPI_PORT=8080

- **Smart Timeouts** - Optimized timeouts with DNS caching- **Adaptive Resilience** – Graceful degradation when external services fail

# Optional: GitHub update checker configuration

# GITHUB_REPO=klept0/TestFlight_Apprise_Notifier- **Comprehensive Logging** - Python's logging module for better log management- **Enhanced Validation** – Format validation for TestFlight IDs (8-12 alphanumeric characters) before network checks

# GITHUB_BRANCH=main

# GITHUB_CHECK_INTERVAL_HOURS=24  # Check every 24 hours (set to 0 to disable)- **Adaptive Resilience** - Graceful degradation when external services fail

```

- **Enhanced Validation** - Format validation for TestFlight IDs before network checks---

---

- **GitHub Update Checker** - Automatic monitoring for repository updates with notifications and manual check via APIUses **FastAPI** for the server, **Apprise** for notifications, and **aiohttp** for asynchronous HTTP requests.

## Running the Application



Start the script using:

------

```bash

python main.py

```

## Setup## ✨ Features

The FastAPI server will be accessible via the URL shown in the console, displaying the actual IP address (e.g., `http://192.168.1.100:8080`).



---

### Prerequisites✅ **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability.  

## Application Control

🔔 **Notifications** – Sends alerts using Apprise when slots open up, including app icons as attachments for supported services (e.g., Discord, Slack).  

The TestFlight Apprise Notifier runs as a **single Python process** with multiple concurrent async tasks (monitoring, heartbeat, web server). The stop and restart functionality works as follows:

- Python 3.8 or higher❤️ **Heartbeat Notifications** – Sends periodic status updates to ensure the bot is active.  

### Stop Functionality

- Install dependencies:📜 **Logging** – Uses Python's `logging` module for better log management.  

- **Process** - Single-process application with async task coordination

- **Mechanism** - Sets a shutdown event that gracefully stops all running tasks🛑 **Graceful Shutdown** – Cleans up resources properly on exit.  

- **Cleanup** - Properly closes HTTP connections and cleans up resources

- **Notification** - Sends Apprise notification about the manual stop```bash🔧 **Environment Variable Validation** – Ensures required configurations are set before starting.  

- **Result** - Clean shutdown without data loss

pip install -r requirements.txt🎨 **App Name Extraction** – Accurately extracts and displays app names from TestFlight pages.  

### Restart Functionality

```🌐 **Web Dashboard** – FastAPI-powered web interface with real-time status, logs, and monitoring statistics.  

- **Process** - Spawns a new Python process using `subprocess.Popen`

- **Mechanism** - New instance starts immediately, then current instance shuts down🔧 **Dynamic ID Management** – Add/remove TestFlight IDs through the web dashboard without restarting the application.  

- **State** - Configuration persists via `.env` file updates

- **Notification** - Sends Apprise notification about the restart### Environment Variables📱 **Mobile-Friendly UI** – Responsive design that works perfectly on phones, tablets, and desktops.  

- **Zero-downtime** - New process starts before old one stops

🎛️ **Interactive Management** – Collapsible cards for organized TestFlight ID management.  

### Service Operation

Create a `.env` file in the project root with these values:📡 **RESTful API** – Complete API endpoints for status, logs, and TestFlight ID management.  

- **Not a system service** - Runs as a regular Python application

- **Manual control** - Use web dashboard buttons or send signals (Ctrl+C)🛑 **Web-based Application Control** – Stop and restart the application directly from the web dashboard.  

- **Process management** - Can be managed with tools like `systemd`, `supervisor`, or `pm2`

- **Resource efficient** - Single process with async I/O, minimal memory footprint```ini🎨 **Enhanced UI Aesthetics** – Modern gradient buttons with professional styling and responsive design.  



---# List of TestFlight IDs to monitor (comma-separated)🛡️ **Security Verified** – Repository confirmed to contain no actual secrets, only test/example data.  



## Web DashboardID_LIST=abc123,def456,ghi789🏥 **Health Monitoring** – Comprehensive health check endpoint with system metrics and performance monitoring.  



The web interface provides:🚀 **HTTP Optimization** – Connection pooling, DNS caching, and keep-alive for 60-80% performance improvement.  



- **Real-time Status** - Bot status, version, uptime, and monitoring statistics# Apprise notification URLs (comma-separated for multiple services)⚡ **Circuit Breaker** – Automatic failure detection and recovery for external service resilience.  

- **Live Logs** - Recent activity with color-coded log levels and timestamps

- **TestFlight ID Management** - Add/remove monitored apps through the web interfaceAPPRISE_URL=mailto://user:password@smtp.example.com,discord://webhook_id/webhook_token🧠 **Smart Caching** – LRU caches with size limits prevent memory leaks while maintaining performance.  

- **Apprise URL Management** - Add/remove notification URLs with service logos

- **Mobile-Responsive Design** - Optimized for phones, tablets, and desktops⚡ **Rate Limiting** – Prevents API throttling with configurable sliding window algorithm.  

- **Interactive Cards** - Collapsible sections with clean icons

- **Auto-refresh** - Dashboard updates every 30 seconds# Interval in milliseconds between checks🔄 **Retry Logic** – Exponential backoff with jitter handles transient failures gracefully.  

- **Application Control** - Stop and restart buttons with confirmation dialogs

INTERVAL_CHECK=10000📊 **Metrics Tracking** – Monitor check statistics, success rates, and status distributions.  

### Apprise Service Icons

📦 **Batch Operations** – Efficiently manage multiple TestFlight IDs in a single request.  

The dashboard displays official service icons for configured Apprise notification URLs instead of showing long text strings. This provides:

# Optional: Heartbeat interval in hours (default: 6)✅ **Enhanced Validation** – Format checking ensures valid TestFlight IDs before processing.  

- **Visual Recognition** - Instantly identify services by their logos

- **Cleaner UI** - Service name and icon instead of full URL textHEARTBEAT_INTERVAL=6🧪 **Unit Tests** – Comprehensive test coverage with pytest for reliability.  

- **Better Organization** - Two-line card layout with masked credentials

- **40+ Services Supported** - Discord, Slack, Telegram, Signal, Pushover, and many more🔄 **GitHub Update Checker** – Automatic monitoring for repository updates with notifications and manual check via API.



For technical details, see [APPRISE_ICON_DISPLAY.md](APPRISE_ICON_DISPLAY.md).# Optional: FastAPI server host (default: 0.0.0.0)



---FASTAPI_HOST=0.0.0.0---



## GitHub Update Checker



The application includes an automatic GitHub update checker that monitors the repository for new commits.# Optional: FastAPI server port (default: random 8000-9000)## ✨ Features  



### FeaturesFASTAPI_PORT=8080



- **Periodic Automatic Checks** - Runs every 24 hours by default (configurable)✅ **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability.  

- **Manual Checks via API** - Trigger update checks on-demand using curl

- **Smart Caching** - Avoids unnecessary API calls by caching results# Optional: GitHub update checker configuration🔔 **Notifications** – Sends alerts using Apprise when slots open up, including app icons as attachments for supported services (e.g., Discord, Slack).  

- **Notifications** - Sends Apprise notifications when updates are detected

- **Version Tracking** - Compares current version with latest GitHub commit# GITHUB_REPO=klept0/TestFlight_Apprise_Notifier❤️ **Heartbeat Notifications** – Sends periodic status updates to ensure the bot is active.  



### Manual Update Check# GITHUB_BRANCH=main📜 **Logging** – Uses Python’s `logging` module for better log management.  



Check for updates via curl:# GITHUB_CHECK_INTERVAL_HOURS=24  # Check every 24 hours (set to 0 to disable)🛑 **Graceful Shutdown** – Cleans up resources properly on exit.  



```bash```🔧 **Environment Variable Validation** – Ensures required configurations are set before starting.  

# Check for updates (uses cache if available)

curl http://localhost:8080/api/updates🎨 **App Name Extraction** – Accurately extracts and displays app names from TestFlight pages.  



# Force a fresh check (bypasses cache)---

curl http://localhost:8080/api/updates?force=true

```---



### Configuration## Running the Application



Configure update checking in your `.env` file:## Application Control



```bashStart the script using:

# Check every 24 hours (default), set to 0 to disable

GITHUB_CHECK_INTERVAL_HOURS=24The TestFlight Apprise Notifier runs as a **single Python process** with multiple concurrent async tasks (monitoring, heartbeat, web server). The stop and restart functionality works as follows:



# Monitor a custom repository (optional)```bash

GITHUB_REPO=yourusername/TestFlight_Apprise_Notifier

GITHUB_BRANCH=mainpython main.py### Stop Functionality

```

```

For complete documentation, see [GITHUB_UPDATE_CHECKER.md](GITHUB_UPDATE_CHECKER.md).

- **Process**: Single-process application with async task coordination

---

The FastAPI server will be accessible via the URL shown in the console, displaying the actual IP address (e.g., `http://192.168.1.100:8080`).- **Mechanism**: Sets a shutdown event that gracefully stops all running tasks

## API Endpoints

- **Cleanup**: Properly closes HTTP connections and cleans up resources

### Status & Monitoring

---- **Notification**: Sends Apprise notification about the manual stop

- `GET /` - Web dashboard interface

- `GET /api/status` - Get current bot status, version, uptime, and statistics- **Result**: Clean shutdown without data loss

- `GET /api/logs` - Retrieve recent log entries with filtering options

- `GET /api/health` - Comprehensive health check with cache stats and circuit breaker status## Application Control

- `GET /api/metrics` - Detailed metrics including check counts, success rates, and status distributions

- `GET /api/updates` - Check for GitHub updates (supports `?force=true` parameter)### Restart Functionality



### TestFlight ID ManagementThe TestFlight Apprise Notifier runs as a **single Python process** with multiple concurrent async tasks (monitoring, heartbeat, web server).



- `POST /api/testflight-ids` - Add a new TestFlight ID to monitor- **Process**: Spawns a new Python process using `subprocess.Popen`

  - Request body: `{"testflight_id": "abc123"}`

- `DELETE /api/testflight-ids` - Remove a TestFlight ID from monitoring### Stop Functionality- **Mechanism**: New instance starts immediately, then current instance shuts down

  - Request body: `{"testflight_id": "abc123"}`

- `POST /api/testflight-ids/batch` - Batch add multiple TestFlight IDs- **State**: Configuration persists via `.env` file updates

  - Request body: `{"testflight_ids": ["abc123", "def456", "ghi789"]}`

- `DELETE /api/testflight-ids/batch` - Batch remove multiple TestFlight IDs- **Process**: Single-process application with async task coordination- **Notification**: Sends Apprise notification about the restart

  - Request body: `{"testflight_ids": ["abc123", "def456"]}`

- **Mechanism**: Sets a shutdown event that gracefully stops all running tasks- **Zero-downtime**: New process starts before old one stops

### Apprise URL Management

- **Cleanup**: Properly closes HTTP connections and cleans up resources

- `GET /api/apprise-urls` - Get all configured Apprise URLs with service icons

- `POST /api/apprise-urls` - Add a new Apprise notification URL- **Notification**: Sends Apprise notification about the manual stop### Service Operation

  - Request body: `{"apprise_url": "discord://webhook_id/webhook_token"}`

- `DELETE /api/apprise-urls` - Remove an Apprise notification URL- **Result**: Clean shutdown without data loss

  - Request body: `{"apprise_url": "discord://webhook_id/webhook_token"}`

- **Not a system service**: Runs as a regular Python application

### Application Control

### Restart Functionality- **Manual control**: Use web dashboard buttons or send signals (Ctrl+C)

- `POST /api/stop` - Gracefully stop the application

- `POST /api/restart` - Restart the application (spawns new process)- **Process management**: Can be managed with tools like `systemd`, `supervisor`, or `pm2`



---- **Process**: Spawns a new Python process using subprocess- **Resource efficient**: Single process with async I/O, minimal memory footprint



## Docker Support- **Mechanism**: New instance starts immediately, then current instance shuts down



The application can be deployed using Docker for easier containerization and deployment.- **State**: Configuration persists via .env file updates---



### Quick Start with Docker Compose- **Notification**: Sends Apprise notification about the restart



```bash- **Zero-downtime**: New process starts before old one stops## Setup

# Start the application

docker-compose up -d



# View logs### Service Operation### Prerequisites

docker-compose logs -f



# Stop the application

docker-compose down- **Not a system service**: Runs as a regular Python application- Python 3.8+

```

- **Manual control**: Use web dashboard buttons or send signals (Ctrl+C)- Install dependencies:

### Manual Docker Build

- **Process management**: Can be managed with tools like systemd, supervisor, or pm2

```bash

# Build the image- **Resource efficient**: Single process with async I/O, minimal memory footprint```bash

docker build -t testflight-notifier .

pip install -r requirements.txt

# Run the container

docker run -d \---```

  --name testflight-notifier \

  -p 8080:8080 \

  --env-file .env \

  testflight-notifier## Web Dashboard### Environment Variables

```



For complete Docker documentation, see [DOCKER.md](DOCKER.md).

The web interface provides:Create a `.env` file in the project root with these values:  

---



## Testing

- **Real-time Status** - Bot status, version, uptime, and monitoring statistics```ini

Run the test suite using pytest:

- **Live Logs** - Recent activity with color-coded log levels and timestamps# List of TestFlight IDs to monitor (comma-separated)

```bash

# Install test dependencies- **TestFlight ID Management** - Add/remove monitored apps through the web interfaceID_LIST=abc123,def456,ghi789  

pip install -r tests/requirements-test.txt

- **Apprise URL Management** - Add/remove notification URLs with service logos and icons

# Run all tests

pytest tests/- **Mobile-Responsive Design** - Optimized for phones, tablets, and desktops```ini



# Run with coverage report- **Interactive Cards** - Collapsible sections with clean icons# List of TestFlight IDs to monitor (comma-separated)

pytest tests/ --cov=. --cov-report=html

- **Auto-refresh** - Dashboard updates every 30 secondsID_LIST=abc123,def456,ghi789

# Run specific test file

pytest tests/test_testflight.py- **API Endpoints** - JSON APIs for status, logs, health, metrics, and updates

```

# Apprise notification URLs (comma-separated for multiple services)

The test suite includes:

---APPRISE_URL=mailto://user:password@smtp.example.com,discord://webhook_id/webhook_token

- Unit tests for TestFlight status checking

- Tests for app name extraction

- Validation tests for TestFlight ID format

- Mock-based tests for external API calls## GitHub Update Checker# Interval in milliseconds between checks



---INTERVAL_CHECK=10000



## Configuration DetailsThe application includes an automatic GitHub update checker that monitors the repository for new commits.



### Rate Limiting# Optional: Heartbeat interval in hours (default: 6)



Configure rate limiting to prevent API throttling:### FeaturesHEARTBEAT_INTERVAL=6



```python

# In main.py or .env

RATE_LIMIT_REQUESTS=100  # Maximum requests- **Periodic Automatic Checks** - Runs every 24 hours by default (configurable)# Optional: FastAPI server host (default: 0.0.0.0)

RATE_LIMIT_WINDOW=60     # Time window in seconds

```- **Manual Checks via API** - Trigger update checks on-demand using curlFASTAPI_HOST=0.0.0.0



### Circuit Breaker- **Smart Caching** - Avoids unnecessary API calls by caching results



Configure circuit breaker thresholds:- **Notifications** - Sends Apprise notifications when updates are detected# Optional: FastAPI server port (default: random 8000-9000)



```python- **Version Tracking** - Compares current version with latest GitHub commitFASTAPI_PORT=8080

# In main.py

CIRCUIT_BREAKER_THRESHOLD=5    # Failures before opening

CIRCUIT_BREAKER_TIMEOUT=300    # Timeout in seconds (5 minutes)

```### Manual Update Check# Optional: GitHub update checker configuration



### Caching# GITHUB_REPO=klept0/TestFlight_Apprise_Notifier



Configure caching behavior:Check for updates via curl:# GITHUB_BRANCH=main



```python# GITHUB_CHECK_INTERVAL_HOURS=24  # Check every 24 hours (set to 0 to disable)

# In main.py or .env

CACHE_TTL=300           # Cache time-to-live in seconds```bash```

APP_NAME_CACHE_SIZE=100 # Maximum cache entries

```# Check for updates (uses cache if available)



---curl http://localhost:8080/api/updates---



## Logging



The application uses Python's `logging` module with color-coded output:# Force a fresh check (bypasses cache)## Running the Application



- **INFO** - Normal operational messages (green)curl http://localhost:8080/api/updates?force=true

- **WARNING** - Warning messages (yellow)

- **ERROR** - Error messages (red)```Start the script using:

- **DEBUG** - Detailed diagnostic information



Logs are displayed in:

### Configuration```bash

- Console output (with colors)

- Web dashboard (last 100 entries)python main.py

- API endpoint (`/api/logs`)

Configure update checking in your `.env` file:```

---



## Apprise URL Formats

```bashThe FastAPI server will be accessible via the URL shown in the console, displaying the actual IP address (e.g., `http://192.168.1.100:8080`).

Apprise supports many notification services. Here are some common examples:

# Check every 24 hours (default), set to 0 to disable

```ini

# DiscordGITHUB_CHECK_INTERVAL_HOURS=24---

APPRISE_URL=discord://webhook_id/webhook_token



# Slack

APPRISE_URL=slack://TokenA/TokenB/TokenC# Monitor a custom repository (optional)## Web Dashboard



# TelegramGITHUB_REPO=yourusername/TestFlight_Apprise_Notifier

APPRISE_URL=tgram://bot_token/chat_id

GITHUB_BRANCH=mainThe web interface provides:

# Email (SMTP)

APPRISE_URL=mailto://user:password@smtp.example.com```



# Multiple services (comma-separated)- **Real-time Status** – Bot status, version, uptime, and monitoring statistics

APPRISE_URL=discord://webhook_id/webhook_token,tgram://bot_token/chat_id

```For complete documentation, see [GITHUB_UPDATE_CHECKER.md](GITHUB_UPDATE_CHECKER.md).- **Live Logs** – Recent activity with color-coded log levels and timestamps



For a complete list of supported services, visit the [Apprise documentation](https://github.com/caronc/apprise).- **TestFlight ID Management** – Add/remove monitored apps through the web interface



------- **Apprise URL Management** – Add/remove notification URLs dynamically



## License- **Mobile-Responsive Design** – Optimized for phones, tablets, and desktops



This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.## Enhanced TestFlight Status Checking- **Interactive Cards** – Collapsible sections with clean plus/minus icons



---- **Auto-refresh** – Dashboard updates every 30 seconds



## ChangelogThe application includes an enhanced TestFlight status checking utility (`utils/testflight.py`) that provides:- **API Endpoints** – JSON APIs for status (`/api/status`), logs (`/api/logs`), and health (`/api/health`)



For a detailed history of changes, see [CHANGELOG.md](CHANGELOG.md).



---### Features---



## Contributing



Contributions are welcome! Please feel free to submit issues or pull requests.- **Structured Status Detection** - Uses TestFlightStatus enum (OPEN, FULL, CLOSED, UNKNOWN, ERROR)## GitHub Update Checker



---- **Multiple Detection Patterns** - Robust text pattern matching for accurate status detection



## Acknowledgments- **Optional Caching** - Reduce redundant requests with configurable TTL (default: 5 minutes)The application includes an automatic GitHub update checker that monitors the repository for new commits:



- **FastAPI** - Modern web framework for building APIs- **Better Error Handling** - Detailed error messages and categorization

- **Apprise** - Universal notification library supporting 90+ services

- **aiohttp** - Asynchronous HTTP client/server framework- **Async-First Design** - Efficient concurrent checking using shared HTTP sessions### Features



---- **Structured Return Values** - Complete data including app name, status, errors, and cache info



## Support- **Periodic Automatic Checks** – Runs every 24 hours by default (configurable)



If you encounter any issues or have questions, please open an issue on the GitHub repository.### Enabling Status Caching- **Manual Checks via API** – Trigger update checks on-demand using curl


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
