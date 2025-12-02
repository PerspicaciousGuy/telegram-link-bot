# Telegram Link Remover Bot

A powerful Telegram bot to automatically delete links in your groups. It supports advanced link detection, whitelisting, warnings, and logging.

## 🚀 Features
- **Advanced Link Detection**: Detects links in text, media captions, and hidden text links (Markdown/HTML).
- **Whitelist System**: Allow specific domains (e.g., `youtube.com`) or specific users to post links.
- **Warning System**: Warns users when they post a link. Mutes them for 24 hours after 3 warnings.
- **Logging**: Forwards deleted messages to a private log channel.
- **Admin Commands**: Manage whitelist and warnings easily.
- **Keyword Blacklist**: Automatically delete messages containing banned words.
- **Auto-Delete**: Bot messages (warnings, confirmations) auto-delete after 5 minutes to keep chat clean.
- **Anonymous Admin Support**: Works perfectly with "Group Manager" (Anonymous Admins).
- **MongoDB Support**: Persist warnings, whitelist, and blacklist in the cloud.

## 🛠 Commands
- `/start` - (PM Only) Check if the bot is alive and see developer info.
- `/whitelist <domain>` - (Admin Only) Allow a specific domain (e.g., `/whitelist youtube.com`).
- `/whitelist` (Reply) - (Admin Only) Allow a specific user to post any link.
- `/unlist <domain>` - (Admin Only) Remove a domain from the whitelist.
- `/unlist` (Reply) - (Admin Only) Remove a user from the whitelist.
- `/blacklist <word>` - (Admin Only) Ban a specific word. Messages with this word will be deleted.
- `/unblacklist <word>` - (Admin Only) Unban a word.
- `/list` - (Admin Only) View all whitelisted domains/users and blacklisted words.
- `/unwarn` (Reply) - (Admin Only) Reset warnings for a user **AND** automatically unmute them.
- **Unmute Button** - (Admin Only) Click the button on the "Muted" message to instantly unmute the user.

## ⚙️ Environment Variables
| Variable | Description | Required |
| :--- | :--- | :--- |
| `API_ID` | Your Telegram API ID (from my.telegram.org) | Yes |
| `API_HASH` | Your Telegram API Hash (from my.telegram.org) | Yes |
| `BOT_TOKEN` | Your Bot Token (from @BotFather) | Yes |
| `MONGO_URL` | MongoDB Connection String (for database) | Yes |
| `LOG_CHANNEL_ID` | Channel ID for logs (e.g., -100xxxx) | No |
| `PORT` | Port for web service (Default: 8080) | No |

## 🚀 Deployment

### Deploy on Koyeb
1.  **Fork this repository**.
2.  Create a new App on [Koyeb](https://www.koyeb.com).
3.  Select **GitHub** as source and choose your forked repo.
4.  Add the **Environment Variables** listed above.
5.  Set the port to **8080**.
6.  Deploy!

### Deploy Locally
1.  Clone the repo:
    ```bash
    git clone https://github.com/PerspicaciousGuy/telegram-link-bot.git
    cd telegram-link-bot
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set environment variables in a `.env` file or your terminal.
4.  Run the bot:
    ```bash
    python bot.py
    ```

## 👨‍💻 Developer
Built by [Justinixx](https://t.me/justinixx).
