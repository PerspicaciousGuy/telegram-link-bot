import os
import os
import re
import asyncio
from datetime import datetime, timedelta
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

# Helper for auto-deleting messages
async def scheduled_delete(message, delay=300):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass

def is_admin(chat_member):
    return chat_member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]

@app.on_message(filters.command("ping"))
async def ping_command(client, message):
@app.on_message(filters.command("ping"))
async def ping_command(client, message):
    await message.reply("Pong! 🏓\nI am alive.")

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):

    text = (
        "👋 **Hello! I am the Link Remover Bot.**\n\n"
        "I help keep your group clean by automatically deleting links sent by non-admins.\n\n"
        "**My Features:**\n"
        "🔹 Delete text links, media captions, and hidden links.\n"
        "🔹 Whitelist specific domains or users.\n"
        "🔹 Warn users and mute them after 3 strikes.\n"
        "🔹 Log deleted messages to a channel.\n\n"
        "Add me to your group and promote me to Admin!"
    )
    buttons = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/justinixx")],
        [types.InlineKeyboardButton("📦 Source Code", url="https://github.com/PerspicaciousGuy/telegram-link-bot")]
    ])
    await message.reply(text, reply_markup=buttons, disable_web_page_preview=True)



# --- Admin Commands ---

@app.on_message(filters.command("whitelist") & filters.group)
async def whitelist_command(client, message):
    # Check Admin (Handle Anonymous Admin)
    is_sender_admin = False
    if not message.from_user:
        if message.sender_chat and message.sender_chat.id == message.chat.id:
            is_sender_admin = True
    else:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        is_sender_admin = is_admin(member)

    if not is_sender_admin:
        return

    if len(message.command) < 2:
        await message.reply("Usage: `/whitelist <domain>` or reply to a user to whitelist them.")
        return

    target = message.command[1]
    
    # If reply, whitelist user
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        try:
            await db.add_whitelist_user(target_user.id)
            msg = await message.reply(f"✅ **User Whitelisted!**\n{target_user.mention} has been added to the database.\nThey can now send links without being restricted.")
            asyncio.create_task(scheduled_delete(msg, delay=300))
        except Exception as e:
            await message.reply(f"❌ **Database Error:** {e}")
        return

    # Else whitelist domain
    try:
        await db.add_whitelist_domain(target)
        msg = await message.reply(f"✅ **Domain Whitelisted!**\nThe domain `{target}` has been added to the database.\nLinks containing this domain will now be ignored by the bot.")
        asyncio.create_task(scheduled_delete(msg, delay=300))
    except Exception as e:
        await message.reply(f"❌ **Database Error:** {e}")

@app.on_message(filters.command("unlist") & filters.group)
async def unlist_command(client, message):
    # Check Admin (Handle Anonymous Admin)
    is_sender_admin = False
    if not message.from_user:
        if message.sender_chat and message.sender_chat.id == message.chat.id:
            is_sender_admin = True
    else:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        is_sender_admin = is_admin(member)

    if not is_sender_admin:
        return

    if len(message.command) < 2:
        await message.reply("Usage: `/unlist <domain>` or reply to a user to remove them from whitelist.")
        return

    target = message.command[1]
    
    # If reply, unlist user
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        try:
            await db.remove_whitelist_user(target_user.id)
            msg = await message.reply(f"✅ **User Unlisted!**\n{target_user.mention} has been removed from the whitelist.\nTheir links will now be deleted.")
            asyncio.create_task(scheduled_delete(msg, delay=300))
        except Exception as e:
            await message.reply(f"❌ **Database Error:** {e}")
        return

    # Else unlist domain
    try:
        await db.remove_whitelist_domain(target)
        msg = await message.reply(f"✅ **Domain Unlisted!**\nThe domain `{target}` has been removed from the whitelist.\nLinks containing this domain will now be deleted.")
        asyncio.create_task(scheduled_delete(msg, delay=300))
    except Exception as e:
        await message.reply(f"❌ **Database Error:** {e}")

@app.on_message(filters.command("unwarn") & filters.group)
async def unwarn_command(client, message):
    # Check Admin (Handle Anonymous Admin)
    is_sender_admin = False
    if not message.from_user:
        if message.sender_chat and message.sender_chat.id == message.chat.id:
            is_sender_admin = True
    else:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        is_sender_admin = is_admin(member)

    if not is_sender_admin:
        return

    if not message.reply_to_message:
        await message.reply("Reply to a user to reset their warnings.")
        return
    
    target_user = message.reply_to_message.from_user
    
    # Reset warnings
    try:
        await db.reset_warnings(target_user.id)
    except Exception as e:
        await message.reply(f"❌ **Database Error (Reset Warnings):** {e}")
        return
    
    # Also Unmute to ensure they can chat
    try:
        await client.restrict_chat_member(
            message.chat.id,
            target_user.id,
            types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
        )
    except Exception:
        pass # If fails (e.g. user not muted), just ignore

    msg = await message.reply(f"✅ **Warnings Reset!**\nWarnings for {target_user.mention} have been cleared.\nThey have been unmuted and can now send messages again.")
    asyncio.create_task(scheduled_delete(msg, delay=300))

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
            until_date = datetime.now() + timedelta(hours=24)
            await client.restrict_chat_member(
                chat_id, 
                user_id, 
                types.ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            
            # Unmute Button
            button = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("🔓 Unmute (Admin Only)", callback_data=f"unmute_{user_id}")]
            ])
            
            await message.reply(f"🚫 {message.from_user.mention} has been muted for 24h due to excessive links.", reply_markup=button)
            await db.reset_warnings(user_id)
        except Exception as e:
            await message.reply(f"⚠️ {message.from_user.mention}, stop sending links! (Warning {warnings}/{limit})\nI tried to mute you but failed: {e}")
    else:
        msg = await message.reply(f"⚠️ {message.from_user.mention}, links are not allowed! (Warning {warnings}/{limit})")
        asyncio.create_task(scheduled_delete(msg, delay=300))

@app.on_callback_query(filters.regex(r"^unmute_"))
async def unmute_callback(client, callback_query):
    # Check Admin
    member = await client.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
    if not is_admin(member):
        await callback_query.answer("❌ Only admins can unmute!", show_alert=True)
        return

    target_user_id = int(callback_query.data.split("_")[1])
    chat_id = callback_query.message.chat.id

    try:
        # Unmute User (Give back default permissions)
        await client.restrict_chat_member(
            chat_id,
            target_user_id,
            types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
        )
        
        # Reset Warnings
        await db.reset_warnings(target_user_id)
        
        # Update Message
        admin_name = callback_query.from_user.mention
        await callback_query.message.edit_text(f"✅ User unmuted by {admin_name}.\nWarnings have been reset.")
        asyncio.create_task(scheduled_delete(callback_query.message, delay=300))
        
    except Exception as e:
        await callback_query.answer(f"Failed to unmute: {e}", show_alert=True)

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

from pyrogram import idle

async def main():
    await app.start()
    print("Bot is running...")
    
    if log_channel_id != 0:
        try:
            await app.send_message(log_channel_id, "✅ **Bot has restarted!**\nI am now online and protecting your groups.")
        except Exception as e:
            print(f"Failed to send restart log: {e}")

    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
