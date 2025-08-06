# TeleScout

A Python application that monitors Telegram channels for specific keywords and forwards matching messages to you. Perfect for tracking mentions, news, trading signals, or any other keywords across multiple channels.

## Features

- 🔍 **Keyword Matching**: Monitor multiple channels for specific keywords with smart word boundary detection
- ⏰ **Historical Scanning**: Scan past messages within a configurable time window
- 🚀 **Real-time Monitoring**: Continuously monitor channels for new messages
- 📨 **Message Forwarding**: Automatically forward matching messages with context and formatting
- ⚡ **Rate Limiting**: Built-in flood protection and configurable delays
- 📊 **Comprehensive Logging**: Detailed logging with file output support
- 🛡️ **Error Handling**: Robust error handling for network issues and API limits

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Create a new application
3. Note down your `api_id` and `api_hash`

### 3. Get Your User ID or Group ID

**For forwarding to yourself (Saved Messages):**
- Get your user ID by messaging @userinfobot on Telegram

**For forwarding to a group:**
- Use the included helper script to list your groups:
  ```bash
  python list_groups.py
  ```
- Find the group you want to use and copy its ID from the "Config format" line

### 4. Configure the Application

```bash
# Copy configuration template
cp config.example.yaml config.yaml

# Copy environment template (optional)
cp .env.example .env
```

Edit `config.yaml` with your settings:
- Add your Telegram API credentials
- Set your user ID or group ID for message forwarding
- Configure channels to monitor (usernames or IDs)
- Add keywords to search for

## Usage

### Basic Usage

```bash
python main.py
```

### Command Line Options

```bash
python main.py --help
```

Options:
- `--config`: Specify config file path (default: config.yaml)
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--no-log-file`: Disable logging to file
- `--scan-only`: Only scan historical messages, don't monitor real-time
- `--no-historical`: Skip historical scan, only monitor real-time

### Examples

```bash
# Scan historical messages only
python main.py --scan-only

# Monitor in real-time only (skip historical)
python main.py --no-historical

# Use custom config file with debug logging
python main.py --config my-config.yaml --log-level DEBUG
```

## Configuration

The `config.yaml` file contains all settings:

```yaml
telegram:
  api_id: YOUR_API_ID
  api_hash: "YOUR_API_HASH"
  phone_number: "+1234567890"

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
```

## Security

### Built-in Security Features

**Rate Limiting Protection:**
- Global limit: Maximum 60 messages per hour (default)
- Per-channel limit: Maximum 20 messages per channel per hour (default)
- Configurable delays between forwards
- Automatic rate limit enforcement to prevent spam

**Message Security:**
- Message length limits to prevent extremely long messages
- Content sanitization and truncation
- Safe handling of malicious content

**File Security:**
- Session files automatically secured with restricted permissions (600)
- Configuration validation on startup
- Automatic detection of placeholder/default credentials

**Authentication Security:**
- Session-based authentication (no password storage)
- Automatic session file protection
- Credential validation

### Security Configuration

Add these optional security settings to your `config.yaml`:

```yaml
# Security Settings (optional)
max_messages_per_hour: 60        # Global message limit
max_messages_per_channel_per_hour: 20  # Per-channel limit  
max_message_length: 4000         # Message length limit
```

### Security Best Practices

**File Permissions:**
```bash
# Secure your config files
chmod 600 config.yaml .env

# Check current permissions
ls -la config.yaml .env *.session
```

**Monitoring:**
- Regularly check forwarded message volume
- Monitor logs for rate limiting warnings
- Review forwarded content periodically

**Account Safety:**
- Use a dedicated Telegram account if possible
- Enable 2FA on your Telegram account
- Regularly review active sessions in Telegram settings
- Never share session files or API credentials

### Security Warnings

The application will warn you about:
- Insecure file permissions
- Default/placeholder credentials
- Rate limit violations
- Suspicious message patterns

### Potential Risks

**Message Flooding:** Even with rate limits, high-traffic channels could generate many matches. Monitor your groups.

**Account Access:** Session files contain account access. Keep them secure and never commit to version control.

**Dependency Security:** Keep dependencies updated. Use `pip install -r requirements.txt --upgrade` periodically.

## Troubleshooting

### Common Issues

1. **"Could not find target user"**: Make sure your `forward_to_user_id` is correct
2. **"Could not resolve channel"**: Ensure channel usernames are correct and you have access
3. **Authentication errors**: Check your API credentials and phone number
4. **Flood wait errors**: The application handles these automatically with delays

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

## License

MIT License - see LICENSE file for details.
