# 🚀 TestFlight Apprise Notifier  

📡 **Monitors TestFlight beta links and sends notifications when a beta becomes available!**  
Uses **FastAPI** for the server, **Apprise** for notifications, and **aiohttp** for asynchronous HTTP requests.

---

## ✨ Features  

✅ **TestFlight Monitoring** – Automatically checks TestFlight beta links for availability.  
🔔 **Notifications** – Sends alerts using Apprise when slots open up.  
❤️ **Heartbeat Notifications** – Sends periodic status updates to ensure the bot is active.  
📜 **Logging** – Uses Python’s `logging` module for better log management.  
🛑 **Graceful Shutdown** – Cleans up resources properly on exit.  
🔧 **Environment Variable Validation** – Ensures required configurations are set before starting.  

---

## 📦 Setup  

### **🔧 Prerequisites**  

- 🐍 **Python 3.8+**  
- 📦 Install dependencies:  
  ```bash
  pip install -r requirements.txt
  ```

### **⚙️ Environment Variables**  

Create a `.env` file in the project root with these values:  

```ini
# List of TestFlight IDs to monitor (comma-separated)
ID_LIST=abc123,def456,ghi789  

# Apprise notification URLs (comma-separated for multiple services)
APPRISE_URL=mailto://user:password@smtp.example.com,discord://webhook_id/webhook_token  

# Interval in milliseconds between checks
INTERVAL_CHECK=10000  
```

---

## 🚀 Running the Application  

Start the script using:  
```bash
python main.py
```
The FastAPI server will be accessible via URL shown in the console like this: **[http://localhost:8xxx](http://localhost:8xxx)**  

---

## 🛠 Utility Functions  

🔹 **`utils/notifications.py`** – Handles notifications with error handling.  
🔹 **`utils/formatting.py`** – Provides functions for formatting dates & links.  
🔹 **`utils/colors.py`** – Adds color-coded console output for better visibility.  

---

## 📜 Logging  

The application logs messages in the console with timestamps and log levels:  

```plaintext
2025-04-02 12:00:00 - INFO - Notification sent: Heartbeat - 2025-04-02 12:00:00  
2025-04-02 12:01:00 - INFO - 200 - abc123 - AppName - Available  
Notification sent: https://testflight.apple.com/join/abc123  
```

---

## ❤️ Heartbeat Notifications  

To confirm the bot is running, it sends a **heartbeat notification every 6 hours.**  

✅ **Example Heartbeat Message:**  
```plaintext
2025-04-02 18:00:00 - INFO - Notification sent: Heartbeat - 2025-04-02 18:00:00
```

---

## 🛑 Graceful Shutdown  

The bot handles **SIGINT** and **SIGTERM** signals to properly close connections before stopping.  

---

## 🤝 Contributing  

Want to help improve this project? Feel free to **submit issues** or **create a pull request**!  

---

## 📜 License  

This project is licensed under the **MIT License**.  

---

## 📦 Releases

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
