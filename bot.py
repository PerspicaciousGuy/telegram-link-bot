import os
import re
import asyncio
from pyrogram import Client, filters, types, enums
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from database import Database

# Telegram bot credentials
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")
log_channel_id = int(os.environ.get("LOG_CHANNEL_ID", 0))

app = Client("link_remover_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
db = Database()

# Regex pattern for links
url_pattern = re.compile(r"(https?://\S+|www\.\S+)")

def is_admin(chat_member):
    return chat_member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]

@app.on_message(filters.group & (filters.text | filters.caption))
async def link_handler(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0
    
    # 1. Check if user is Admin/Owner (Immune)
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if is_admin(member):
            return
    except Exception:
        pass # Failed to get member, proceed with caution or return

    # 2. Check Whitelist (User)
    if await db.is_user_whitelisted(user_id):
        return

    # 3. Detect Links
    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []
    
    has_link = False
    
    # Check regex
    if url_pattern.search(text):
        has_link = True
    
    # Check entities (Text Links)
    for entity in entities:
        if entity.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]:
            has_link = True
            break

    if not has_link:
        return

    # 4. Check Whitelist (Domain)
    if await db.is_domain_whitelisted(text):
        return

    # 5. Action: Delete & Warn
    try:
        await message.delete()
    except Exception as e:
        print(f"Failed to delete message: {e}")
        return # If can't delete, maybe can't warn either

    # Log to Channel
    if log_channel_id != 0:
        try:
            log_text = f"**Link Deleted**\n**User:** {message.from_user.mention} (`{user_id}`)\n**Chat:** {message.chat.title}\n**Content:** {text[:1000]}"
            await client.send_message(log_channel_id, log_text)
        except Exception as e:
            print(f"Failed to log: {e}")

    # Warn User
    warnings = await db.add_warning(user_id)
    limit = 3
    
    if warnings >= limit:
        # Punish
        try:
            # Mute for 24 hours
            until_date = asyncio.get_event_loop().time() + 86400
            await client.restrict_chat_member(
                chat_id, 
                user_id, 
                types.ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            await message.reply(f"🚫 {message.from_user.mention} has been muted for 24h due to excessive links.")
            await db.reset_warnings(user_id)
        except Exception as e:
            await message.reply(f"⚠️ {message.from_user.mention}, stop sending links! (Warning {warnings}/{limit})\nI tried to mute you but failed: {e}")
    else:
        msg = await message.reply(f"⚠️ {message.from_user.mention}, links are not allowed! (Warning {warnings}/{limit})")
        # Delete warning after a few seconds to keep chat clean
        await asyncio.sleep(10)
        try:
            await msg.delete()
        except:
            pass

# --- Admin Commands ---

@app.on_message(filters.command("whitelist") & filters.group)
async def whitelist_command(client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if not is_admin(member):
        return

    if len(message.command) < 2:
        await message.reply("Usage: `/whitelist <domain>` or reply to a user to whitelist them.")
        return

    target = message.command[1]
    
    # If reply, whitelist user
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user.id
        await db.add_whitelist_user(target_user)
        await message.reply(f"User {target_user} whitelisted.")
        return

    # Else whitelist domain
    await db.add_whitelist_domain(target)
    await message.reply(f"Domain `{target}` whitelisted.")

@app.on_message(filters.command("unwarn") & filters.group)
async def unwarn_command(client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if not is_admin(member):
        return

    if not message.reply_to_message:
        await message.reply("Reply to a user to reset their warnings.")
        return
    
    target_user = message.reply_to_message.from_user.id
    await db.reset_warnings(target_user)
    await message.reply(f"Warnings reset for {message.reply_to_message.from_user.mention}.")

# Dummy HTTP server to satisfy Koyeb Web Service health check
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

# Start HTTP server in a separate thread
Thread(target=run_server).start()

print("Bot is running...")
app.run()
