# TeleScout

A Python application that monitors Telegram channels for specific keywords and forwards matching messages to you. Features both a command-line interface and a user-friendly web GUI for easy configuration and monitoring.

## Features

- 🖥️ **Web GUI Interface**: Modern web-based dashboard for easy configuration and monitoring
- 🔍 **Keyword Matching**: Monitor multiple channels for specific keywords with smart word boundary detection
- ⏰ **Historical Scanning**: Scan past messages within a configurable time window
- 🚀 **Real-time Monitoring**: Continuously monitor channels for new messages
- 📨 **Message Forwarding**: Automatically forward matching messages with context and formatting
- ⚡ **Rate Limiting**: Built-in flood protection and configurable delays
- 📊 **Comprehensive Logging**: Detailed logging with file output support
- 🛡️ **Error Handling**: Robust error handling for network issues and API limits
- 🎛️ **Dual Interfaces**: Use either command-line or web GUI

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Create a new application
3. Note down your `api_id` and `api_hash`

### 3. Configure the Application

```bash
# Copy configuration template
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your settings or use the web GUI (see Usage section).

### 4. Run TeleScout

**Option A: Web GUI (Recommended)**
```bash
python main.py --gui
```
This opens a web interface at http://localhost:5000 where you can:
- Configure all settings through forms
- Start/stop monitoring with buttons
- Run historical scans only
- Monitor real-time status

**Option B: Command Line**
```bash
python main.py
```

## Usage

### Web GUI Mode

Launch the web interface:
```bash
python main.py --gui
```

The web GUI provides:

**🏠 Home Dashboard:**
- Start/Stop monitoring controls
- Real-time status display
- Configuration summary
- Quick action buttons

**⚙️ Configuration:**
- Telegram API settings
- General settings (user ID, time windows)
- Security settings (rate limits)

**🏷️ Keywords Management:**
- Add/remove keywords to monitor
- Live keyword list

**📡 Channels Management:**
- Add/remove channels to monitor
- Support for @usernames and numeric IDs

**📊 Monitoring:**
- Real-time monitoring status
- Statistics and counters
- Uptime tracking

### Command Line Mode

```bash
# Basic usage - historical scan + real-time monitoring
python main.py

# Scan historical messages only (like GUI "Scan Only" button)
python main.py --scan-only

# Real-time monitoring only (skip historical)
python main.py --no-historical

# Use custom config file with debug logging
python main.py --config my-config.yaml --log-level DEBUG
```

### Command Line Options

```bash
python main.py --help
```

Options:
- `--gui`: Launch web GUI interface
- `--config`: Specify config file path (default: config.yaml)
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--no-log-file`: Disable logging to file
- `--scan-only`: Only scan historical messages, don't monitor real-time
- `--no-historical`: Skip historical scan, only monitor real-time

## Configuration

### Get Your User ID or Group ID

**For forwarding to yourself (Saved Messages):**
- Get your user ID by messaging @userinfobot on Telegram

**For forwarding to a group:**
- Use the included helper script to list your groups:
  ```bash
  python list_groups.py
  ```
- Find the group you want to use and copy its ID from the "Config format" line

### Configuration File

The `config.yaml` file contains all settings. You can edit it manually or use the web GUI:

```yaml
telegram:
  api_id: YOUR_API_ID
  api_hash: "YOUR_API_HASH"
  phone_number: "+1234567890"
  session_name: "telescout_session"

forward_to_user_id: YOUR_USER_ID_OR_GROUP_ID

channels:
  - "@channel1"
  - "@channel2"
  - "-1001234567890"  # Channel ID format

keywords:
  - "keyword1"
  - "phrase with spaces"
  - "case insensitive"

time_window_hours: 24  # Optional: hours to scan backwards
forward_delay: 5       # Seconds between forwards

# Security Settings (optional)
max_messages_per_hour: 60        # Global message limit
max_messages_per_channel_per_hour: 20  # Per-channel limit  
max_message_length: 4000         # Message length limit
```

## Security

### 🚨 Important Security Information

**This application is designed for personal use only. Each user runs their own instance with their own API credentials.**

### Built-in Security Features

**Rate Limiting Protection:**
- **Global limit**: Maximum 60 messages per hour (configurable)
- **Per-channel limit**: Maximum 20 messages per channel per hour (configurable)
- Configurable delays between forwards
- Automatic rate limit enforcement to prevent spam

**Web GUI Security:**
- Binds to localhost (127.0.0.1) only - not accessible from network
- Random session keys generated on startup
- No data transmission to external servers
- All processing happens locally

**File Security:**
- Session files automatically secured with restricted permissions (600)
- Configuration files protected from accidental commits (.gitignore)
- Automatic detection of placeholder/default credentials

**Message Security:**
- Message length limits to prevent extremely long messages
- Content sanitization and truncation
- Safe handling of malicious content

### Security Best Practices

**🔐 API Credentials:**
- **Never share your API credentials** - they provide full account access
- Use your own Telegram account and API credentials
- Enable 2FA on your Telegram account
- Consider using a dedicated Telegram account for monitoring

**📁 File Permissions:**
```bash
# Secure your config files
chmod 600 config.yaml .env

# Check current permissions
ls -la config.yaml .env *.session
```

**🔍 Monitoring:**
- Regularly check forwarded message volume
- Monitor logs for rate limiting warnings
- Review forwarded content periodically
- Use reasonable time windows and rate limits

### What Gets Stored Locally

- **Session files** (*.session): Contains Telegram authentication
- **Configuration files** (config.yaml): Your settings and credentials
- **Log files** (logs/): Application activity logs

### What's Protected

- All sensitive files are in `.gitignore`
- Session files are created with secure permissions
- No credentials are hardcoded in the application
- Web GUI only accepts local connections

### Security Warnings

The application will automatically warn you about:
- Insecure file permissions
- Default/placeholder credentials  
- Rate limit violations
- Configuration security issues

## Troubleshooting

### Common Issues

1. **"Could not find target user"**: Make sure your `forward_to_user_id` is correct
2. **"Could not resolve channel"**: Ensure channel usernames are correct and you have access
3. **Authentication errors**: Check your API credentials and phone number
4. **Flood wait errors**: The application handles these automatically with delays
5. **Web GUI won't start**: Check if port 5000 is already in use

### Finding IDs

**For Groups/Channels you want to forward TO:**
```bash
python list_groups.py
```
This shows all your groups with their IDs in the correct format.

**For Channels you want to MONITOR:**
If you need a channel ID instead of username:
1. Add the bot @username_to_id_bot to your channel
2. Send `/info` command to get the channel ID
3. Use the ID format: `-100XXXXXXXXXX`

### Web GUI Issues

- **Port already in use**: Kill other processes using port 5000, or modify the port in `src/gui.py`
- **Browser doesn't open**: Manually navigate to http://localhost:5000
- **Configuration not saving**: Check file permissions on config.yaml

## Dependencies

- `telethon`: Telegram API client
- `python-dotenv`: Environment variable support
- `pyyaml`: YAML configuration parsing
- `flask`: Web GUI framework

## Architecture

### Command Line Interface
- **main.py**: Application entry point with argument parsing
- **src/config.py**: Configuration management with validation
- **src/telegram_client.py**: Core Telegram client functionality
- **src/keyword_matcher.py**: Keyword detection and matching
- **src/logger.py**: Logging configuration
- **src/security.py**: Security validation and checks

### Web GUI Interface
- **src/gui.py**: Flask web application with monitoring controls
- **templates/**: HTML templates for the web interface
- **static/**: CSS and JavaScript for the web interface

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please ensure all sensitive data remains in configuration files and never hardcoded.