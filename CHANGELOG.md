# 📄 Changelog

## 🚀 v1.0.5 - September 24, 2025

### 🎉 New Features
- ✅ **Dynamic TestFlight ID Management** – Add/remove TestFlight IDs through the web dashboard without restarting
- 🔧 **Web-based Configuration** – Manage monitored apps via the dashboard UI with real-time validation
- 🛡️ **Thread-safe Operations** – Safe concurrent access to ID lists with proper locking
- ✅ **Live Dashboard Updates** – Dashboard reflects changes immediately without page refresh
- 🔍 **ID Validation** – Validates TestFlight IDs before adding to prevent invalid entries
- 💾 **Persistent Configuration** – Changes are saved to `.env` file automatically
- 📱 **Mobile-Responsive Design** – Fully responsive UI that works on phones, tablets, and desktops
- 🎛️ **Interactive UI Elements** – Clean plus/minus icons for collapsible cards
- 🎨 **Enhanced User Experience** – Improved visual design with better spacing and typography

### 🛠 Improvements
- 🔄 **Enhanced Dashboard** – Added management section with add/remove controls
- 📊 **Real-time Statistics** – ID count updates dynamically in the status cards
- ⚡ **API Endpoints** – New REST APIs for ID management (`/api/testflight-ids`)
- 🎨 **UI Enhancements** – Modern management interface with confirmation dialogs
- 🔒 **Input Validation** – Client and server-side validation for all inputs
- 📱 **Responsive Layout** – CSS media queries for optimal viewing on all screen sizes
- 🎯 **Clean Icons** – Replaced complex arrows with universal plus/minus symbols
- 🔔 **Management Notifications** – Apprise notifications sent when IDs are added/removed

### 🐞 Bug Fixes
- 🐛 **Version Display** – Fixed version number display in logs and dashboard
- 🐛 **UI Responsiveness** – Fixed layout issues on mobile devices
- 🐛 **Icon Conflicts** – Resolved doubled-up icon display issues

---

## 🚀 v1.0.4b - September 24, 2025

### 🎉 New Features
- ✅ **Enhanced Web Dashboard** – Complete FastAPI-powered web interface with real-time status, live logs, and API endpoints
- 🔔 **Rich Notifications** – App icons automatically attached to notifications for supported services
- 💾 **Smart Caching** – App names and icons cached to reduce API calls and improve performance
- 🎯 **Intelligent App Detection** – Advanced app name extraction with meta tag fallbacks and expired link detection
- 🔄 **Asynchronous Processing** – Full aiohttp implementation for concurrent monitoring
- 📊 **API Endpoints** – RESTful APIs for status (`/api/status`) and logs (`/api/logs`)
- 🌐 **Auto-Discovery** – Web dashboard shows actual IP address for easy access

### 🛠 Improvements
- 🔧 **Better Error Handling** – Comprehensive exception handling for network failures and parsing errors
- 📜 **Structured Logging** – Color-coded web interface logs with timestamps and levels
- ⚡ **Performance Optimizations** – Concurrent requests and caching for large ID lists
- 🎨 **UI Enhancements** – Modern web dashboard with responsive design and auto-refresh
- 🔧 **Code Quality** – Fixed linting issues and improved code organization

### 🐞 Bug Fixes
- 🐛 **App Name Display** – Fixed "Unknown" app names by implementing better extraction logic
- 🐛 **Resource Management** – Proper async cleanup and signal handling
- 🐛 **Caching Issues** – Resolved cache key conflicts and improved cache reliability

---

## 🚀 v1.0.0 - April 2, 2025

### 🎉 New Features
- ✅ **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability
- 🔔 **Apprise Notifications** – Sends alerts when slots become available
- ❤️ **Heartbeat Notifications** – Sends periodic status updates every 6 hours
- 📜 **Logging** – Uses Python's `logging` module for structured logs
- 🛑 **Graceful Shutdown** – Handles termination signals (`SIGINT`, `SIGTERM`)
- 🔧 **Environment Variable Validation** – Ensures all required configurations are set before execution

### 🛠 Setup & Configuration
- 🐍 **Requires Python 3.8+**
- 📦 **Dependency Installation:** `pip install -r requirements.txt`
- ⚙️ **Uses `.env` file** for configuration (TestFlight IDs, Apprise URLs, check interval)

### 🌐 API & Utility Functions
- 🚀 **FastAPI Server** – Provides a simple API endpoint (`/`) for bot status
- 🔹 **Notification Utility** – Handles Apprise notifications with error handling
- 🔹 **Formatting Utility** – Helper functions for formatting dates & links
- 🔹 **Color-coded Console Output** – Improves log readability

### 🐞 Bug Fixes & Improvements
- 🔄 **Asynchronous Task Management** – Uses `asyncio` for concurrent requests
- 🔄 **Improved Error Handling** – Handles network failures and missing elements gracefully

---

### 📢 Next Steps & Roadmap
- ⏳ **Retry Logic for Failed Requests**
- 📊 **Enhanced Web Dashboard Features**
- ⚡ **Additional Performance Optimizations**

---

### 📌 Release Notes
This version includes significant enhancements to the web dashboard, notification system, and performance optimizations.

📅 *Release Date: September 24, 2025*

---

### 📥 Installation & Usage
Refer to the [README.md](./README.md) for setup instructions and usage details.

🚀 Happy monitoring! 🎉

---

## 🚀 v1.0.4b - September 24, 2025  

### 🎉 New Features  
- ✅ **Enhanced Web Dashboard** – Complete FastAPI-powered web interface with real-time status, live logs, and API endpoints  
- 🔔 **Rich Notifications** – App icons automatically attached to notifications for supported services  
- 💾 **Smart Caching** – App names and icons cached to reduce API calls and improve performance  
- 🎯 **Intelligent App Detection** – Advanced app name extraction with meta tag fallbacks and expired link detection  
- 🔄 **Asynchronous Processing** – Full aiohttp implementation for concurrent monitoring  
- 📊 **API Endpoints** – RESTful APIs for status (`/api/status`) and logs (`/api/logs`)  
- 🌐 **Auto-Discovery** – Web dashboard shows actual IP address for easy access  

### 🛠 Improvements  
- 🔧 **Better Error Handling** – Comprehensive exception handling for network failures and parsing errors  
- 📜 **Structured Logging** – Color-coded web interface logs with timestamps and levels  
- ⚡ **Performance Optimizations** – Concurrent requests and caching for large ID lists  
- 🎨 **UI Enhancements** – Modern web dashboard with responsive design and auto-refresh  
- 🔧 **Code Quality** – Fixed linting issues and improved code organization  

### 🐞 Bug Fixes  
- 🐛 **App Name Display** – Fixed "Unknown" app names by implementing better extraction logic  
- 🐛 **Resource Management** – Proper async cleanup and signal handling  
- 🐛 **Caching Issues** – Resolved cache key conflicts and improved cache reliability  

---

## 🚀 v1.0.0 - April 2, 2025  

### 🎉 New Features  
- ✅ **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability.  
- 🔔 **Apprise Notifications** – Sends alerts when slots become available.  
- ❤️ **Heartbeat Notifications** – Sends periodic status updates every 6 hours.  
- 📜 **Logging** – Uses Python's `logging` module for structured logs.  
- 🛑 **Graceful Shutdown** – Handles termination signals (`SIGINT`, `SIGTERM`).  
- 🔧 **Environment Variable Validation** – Ensures all required configurations are set before execution.  

### 🛠 Setup & Configuration  
- 🐍 **Requires Python 3.8+**  
- 📦 **Dependency Installation:** `pip install -r requirements.txt`  
- ⚙️ **Uses `.env` file** for configuration (TestFlight IDs, Apprise URLs, check interval).  

### 🌐 API & Utility Functions  
- 🚀 **FastAPI Server** – Provides a simple API endpoint (`/`) for bot status.  
- 🔹 **Notification Utility** – Handles Apprise notifications with error handling.  
- 🔹 **Formatting Utility** – Helper functions for formatting dates & links.  
- 🔹 **Color-coded Console Output** – Improves log readability.  

### 🐞 Bug Fixes & Improvements  
- 🔄 **Asynchronous Task Management** – Uses `asyncio` for concurrent requests.  
- 🔄 **Improved Error Handling** – Handles network failures and missing elements gracefully.  

---

### 📢 Next Steps & Roadmap  
- ⏳ **Retry Logic for Failed Requests**  
- 📊 **Enhanced Web Dashboard Features**  
- ⚡ **Additional Performance Optimizations**  

---

### 📌 Release Notes  
This version includes significant enhancements to the web dashboard, notification system, and performance optimizations.  

📅 *Release Date: September 24, 2025*  

---

### 📥 Installation & Usage  
Refer to the [README.md](./README.md) for setup instructions and usage details.  

🚀 Happy monitoring! 🎉